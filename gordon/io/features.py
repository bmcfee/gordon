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

"""Utility functions for dealing with cached features"""

import itertools
import os
import warnings

import numpy as np
import tables

from gordon.db.gordon_db import make_subdirs

warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)

def _args_to_string(kwargs):
    if kwargs:
        s = ''.join('%s%s' % (k,v) for k,v in sorted(kwargs.iteritems()))
    else:
        s = 'None'
    return s

def read_cached_features(filename, feature_extractor, kwargs):
    h5file = None
    try:
        h5file = tables.openFile(filename, mode='r')
        groupname = 'FeatureExtractor%d' % feature_extractor.id

        # Should we ignore names, and walk *all* of the nodes,
        # checking for matching args and kwargs instead of this?
        argstring = _args_to_string(kwargs)
        arrayname = '/'.join(['', groupname, argstring])
        try:
            features = _read_array_from_h5_file(h5file, arrayname,
                                                feature_extractor, kwargs)
        except tables.NoSuchNodeError:
            # FeatureExtractor must have returned a tuple instead of a
            # single array.
            arrays = []
            for n in itertools.count(): 
                curr_arrayname = '%s[%d]' % (arrayname, n)
                try:
                    arrays.append(_read_array_from_h5_file(
                            h5file, curr_arrayname, feature_extractor, kwargs))
                except tables.NoSuchNodeError:
                    break
            features = tuple(arrays)
    finally:
        if h5file:
            h5file.close()

    return features

def _read_array_from_h5_file(h5file, arrayname, feature_extractor, kwargs):
    array = h5file.getNode(arrayname)
    
    # Sanity check.
    #assert feature_extractor.name == array.attrs.feature_extractor_name
    assert kwargs == array.attrs.kwargs
    
    # Copy the array into memory so we don't have to keep the h5
    # file around longer than necessary.
    return np.array(array)


def save_cached_features(filename, feature_extractor, kwargs, features):
    if os.path.exists(filename):
        h5file = tables.openFile(filename, mode='a')
    else:
        make_subdirs(filename)
        h5file = tables.openFile(filename, mode='w')

    groupname = 'FeatureExtractor%d' % feature_extractor.id
    try:
        group = h5file.getNode(h5file.root, groupname)
    except tables.NoSuchNodeError:
        group = h5file.createGroup(h5file.root, groupname,
                                   str(feature_extractor.name))

    arrayname = _args_to_string(kwargs)
    if type(features) is tuple:
        for n,x in enumerate(features):
            curr_arrayname = '%s[%d]' % (arrayname, n)
            _write_array_to_h5_file(h5file, group, curr_arrayname, x,
                                     feature_extractor, kwargs)
    else:
        _write_array_to_h5_file(h5file, group, arrayname, features,
                                feature_extractor, kwargs)

    h5file.close()
        
def _write_array_to_h5_file(h5file, group, arrayname, array, feature_extractor,
                            kwargs):
    array = h5file.createArray(group, arrayname, np.asarray(array))
    array.attrs.feature_extractor_name = str(feature_extractor.name)
    array.attrs.kwargs = kwargs
