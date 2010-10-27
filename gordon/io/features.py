# Copyright (C) 2010 Ron Weiss
#
# This file is part of Gordon.
#
# Gordon is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Gordon is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gordon.  If not, see <http://www.gnu.org/licenses/>.

"""Utility functions for managing gordon features."""

import itertools
import os
import warnings

import matplotlib.pyplot as plt
import numpy as np
import tables

warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)

class CachedFeatureFile(object):
    """Interface to an HDF5 file containing cached features.

    Features are indexed using a gordon FeatureExtractor object and an
    optional set of keyword arguments.
    """
    def __init__(self, filename, mode='r'):
        self.filename = filename
        self.open(mode)

    def open(self, mode='r'):
        self.h5file = tables.openFile(self.filename, mode=mode)

    def close(self):
        self.h5file.close()

    # The contents of the file are organized using a tree structure of
    # the form: "/FeatureExtractorID#/kwargs"
    #
    # This allows a single file to store the output of multiple
    # feature extractors (on a single track), using any number of
    # different settings.  kwargs is a string representing the
    # arguments passed in to Track.feature('name', **kwargs), i.e. a
    # specific configuration of the feature extractor.

    @staticmethod
    def _args_to_string(kwargs):
        if kwargs:
            s = ''.join('%s%s' % (k,v) for k,v in sorted(kwargs.iteritems()))
        else:
            s = 'None'
        return s

    @staticmethod
    def _get_hdf5_path(feature_extractor, kwargs):
        groupname = 'FeatureExtractor%d' % feature_extractor.id
        arrayname = CachedFeatureFile._args_to_string(kwargs)
        return groupname, arrayname

    def has_features(self, feature_extractor, kwargs=None):
        """Check if the file contains a set of features.

        Return True if the file contains features extracted using the
        given FeatureExtractor object with the given kwargs."""
        groupname, arrayname = self._get_hdf5_path(feature_extractor, kwargs)
        try:
            group = self.h5file.getNode(self.h5file.root, groupname)
            array = self.h5file.getNode(group, arrayname)
            # Sanity check.
            assert array.attrs.feature_extractor_id == feature_extractor.id
            assert array.attrs.kwargs == kwargs
            return True
        except tables.NoSuchNodeError:
            try:
                # Check if the cached feature is a tuple.
                group = self.h5file.getNode(self.h5file.root, groupname)
                array = self.h5file.getNode(group, '%s[0]' % arrayname)
                return True
            except tables.NoSuchNodeError:
                return False

    def get_features(self, feature_extractor, kwargs=None):
        """Read cached features from this file.

        Depending on the output of feature_extractor.extract_features,
        this will return either a numpy array or a tuple of numpy arrays.

        Raises tables.NoSuchNodeError if the file doesn't contain
        features corresponding to (feature_extractor, kwargs).
        """
        groupname, arrayname = self._get_hdf5_path(feature_extractor, kwargs)
        group = self.h5file.getNode(self.h5file.root, groupname)

        try:
            features = self._read_features_array(group, arrayname,
                                                 feature_extractor, kwargs)
        except tables.NoSuchNodeError:
            # The FeatureExtractor must have returned a tuple instead
            # of a single array.
            features = self._read_features_tuple(group, arrayname,
                                                 feature_extractor, kwargs)
        return features

    def _read_features_array(self, group, arrayname, feature_extractor,
                             kwargs):
        array = self.h5file.getNode(group, arrayname)
    
        # Sanity check.
        assert array.attrs.feature_extractor_id == feature_extractor.id
        assert array.attrs.kwargs == kwargs
        
        # Copy the array into memory so we don't have to keep the h5
        # file around longer than necessary.
        return np.array(array)
    
    def _read_features_tuple(self, group, arrayname, feature_extractor,
                             kwargs):
        arrays = []
        for n in itertools.count(): 
            curr_arrayname = '%s[%d]' % (arrayname, n)
            try:
                arrays.append(self._read_features_array(
                        group, curr_arrayname, feature_extractor, kwargs))
            except tables.NoSuchNodeError:
                if arrays:
                    break
                else:
                    raise
        return tuple(arrays)

    def list_all_features(self):
        """Return a list of all features contained in this file.

        Each entry of the feature list contains a tuple of the form:
        ('name', FeatureExtractor.name, 'kwarg1', val1, 'kwarg2', val2, ...)
        I.e. the keyword arguments passed to Track.features() to
        compute the corresponding features.
        """
        features_list = []
        for group in self.h5file.iterNodes(self.h5file.root):
            for array in self.h5file.iterNodes(group):
                keylist = ['name', array.attrs.feature_extractor_name]
                for k,v in array.attrs.kwargs.iteritems():
                    keylist.append(k)
                    keylist.append(v)
                features_list.append(tuple(keylist))
        return features_list

    def get_all_features(self):
        """Return a dictionary of all features contained in this file.

        The dictionary is keyed using a tuple of the form:
        ('name', FeatureExtractor.name, 'kwarg1', val1, 'kwarg2', val2, ...)
        I.e. the key corresponds to the keyword arguments passed to
        Track.features() to compute the corresponding features.
        """
        features_dict = {}
        for group in self.h5file.iterNodes(self.h5file.root):
            for array in self.h5file.iterNodes(group):
                keylist = ['name', array.attrs.feature_extractor_name]
                for k,v in array.attrs.kwargs.iteritems():
                    keylist.append(k)
                    keylist.append(v)
                key = tuple(keylist)
                try:
                    if not key in features_dict:
                        features_dict[key] = np.copy(array)
                    else:
                        # Feature must be a tuple.
                        if not isinstance(features_dict[key], tuple):
                            features_dict[key] = (features_dict[key],)
                        feature_list = list(features_dict[key])
                        feature_list.append(np.copy(array))
                        features_dict[key] = tuple(feature_list)
                except TypeError:
                    # This will happen if the cached feature includes
                    # a dict in it's keyword arguments, since dicts
                    # are not hashable.
                    warnings.warn('Ignoring cached feature, name=%s, kwargs=%s'
                                  % (array.attrs.feature_extractor_name,
                                     array.attrs.kwargs.iteritems()))
        return features_dict

    def set_features(self, feature_extractor, features, kwargs=None):
        """Write the given features to this file.

        features must be a numpy array or tuple of numpy arrays.
        """
        groupname, arrayname = self._get_hdf5_path(feature_extractor, kwargs)
        try:
            group = self.h5file.getNode(self.h5file.root, groupname)
        except tables.NoSuchNodeError:
            group = self.h5file.createGroup(self.h5file.root, groupname,
                                            str(feature_extractor.name))

        if isinstance(features, tuple):
            for n,x in enumerate(features):
                curr_arrayname = '%s[%d]' % (arrayname, n)
                self._write_features_array(group, curr_arrayname, x,
                                           feature_extractor, kwargs,
                                           isTuple=True)
        else:
            self._write_features_array(group, arrayname, features,
                                       feature_extractor, kwargs)
    
    def _write_features_array(self, group, arrayname, array, feature_extractor,
                              kwargs, isTuple=False):
        # Should we use createCArray for compression?
        array = self.h5file.createArray(group, arrayname, np.asarray(array))
        array.attrs.feature_extractor_id = feature_extractor.id
        array.attrs.feature_extractor_name = str(feature_extractor.name)
        array.attrs.kwargs = kwargs
        array.attrs.isTuple = isTuple

    def del_features(self, feature_extractor, kwargs=None):
        """Delete cached features from this file.

        Raises tables.NoSuchNodeError if the file doesn't contain
        features corresponding to (feature_extractor, kwargs).
        """
        groupname, arrayname = self._get_hdf5_path(feature_extractor, kwargs)
        try:
            group = self.h5file.getNode(self.h5file.root, groupname)
            self.h5file.removeNode(group, arrayname)
        except tables.NoSuchNodeError:
            # Check if the cached feature is a tuple.
            try:
                deleted_an_array = False
                group = self.h5file.getNode(self.h5file.root, groupname)
                for n in itertools.count(): 
                    self.h5file.removeNode(group, '%s[%d]' % (arrayname, n))
                    deleted_an_array = True
            except:
                if not deleted_an_array:
                    raise

    def del_all_features(self, feature_extractor=None):
        """Delete all cached features from this file.

        If feature_extractor is specified, only delete features
        corresponding to that FeatureExtractor.
        """
        if feature_extractor:
            groupname, arrayname = self._get_hdf5_path(feature_extractor, None)
            self.h5file.removeNode(self.h5file.root, groupname, recursive=True)
        else:
            for group in self.h5file.iterNodes(self.h5file.root):
                self.h5file.removeNode(group, recursive=True)


def plot_features(feats):
    """Default feature plotting function."""
    if isinstance(feats, tuple):
        feats = feats[0]

    COLORBAR_WIDTH = 0.035
    COLORBAR_PAD = 0.015
    
    if feats.ndim == 2:
        plt.imshow(feats.T, origin='lower', interpolation='nearest',
                   aspect='auto')
        plt.colorbar(fraction=COLORBAR_WIDTH, pad=COLORBAR_PAD)
    else: 
        plt.plot(feats)
        # Compensate for colorbar axes in case this figure also
        # contains some images.
        axes = plt.gca()
        bounds = axes.get_position().bounds
        axes.set_position((bounds[0], bounds[1],
                           bounds[2] * (1 - COLORBAR_WIDTH - COLORBAR_PAD),
                           bounds[3]))
    plt.gca().set_xlim((0, len(feats)-1))

