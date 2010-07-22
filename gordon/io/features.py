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

import os

import numpy as np
import tables

from gordon.db.gordon_db import make_subdirs

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
        array = h5file.getNode('/'.join(['', groupname, argstring]))
        
        # Sanity check.
        #assert feature_extractor.name == array.attrs.feature_extractor_name
        assert kwargs == array.attrs.kwargs

        # Copy the array into memory so we don't have to keep the h5
        # file around longer than is necessary.
        nparray = np.array(array)
    finally:
        if h5file:
            h5file.close()

    return nparray

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

    argstring = _args_to_string(kwargs)
    array = h5file.createArray(group, argstring, np.asarray(features))
    array.attrs.feature_extractor_name = str(feature_extractor.name)
    array.attrs.kwargs = kwargs

    h5file.close()
        
