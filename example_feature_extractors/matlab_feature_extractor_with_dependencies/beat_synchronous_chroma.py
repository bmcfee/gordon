import os
import sys
import numpy as np

CURRDIR = os.path.dirname(os.path.abspath(__file__))
MLABWRAPDIR = os.path.join(CURRDIR, 'mlabwrap-1.1')
try:
    from mlabwrap import mlab
except ImportError:
    print 'Unable to import mlab module.  Attempting to install...'
    os.system('cd %s; python setup.py build' % MLABWRAPDIR)
    basedir = '%s/build/' % MLABWRAPDIR
    sys.path.extend([os.path.join(basedir, x) for x in os.listdir(basedir)
                     if x.startswith('lib')])
    from mlabwrap import mlab

mlab.addpath(os.path.join(CURRDIR, 'coversongs'))


def extract_features(track, fctr=400, fsd=1.0, type=1):
    """Computes beat-synchronous chroma features.
    
    Uses Dan Ellis' chrombeatftrs Matlab function.
    """
    x,fs,svals = track.audio()

    feats,beats = mlab.chrombeatftrs(x.mean(1)[:,np.newaxis], fs, fctr, fsd,
                                     type, nout=2)
    songlen = x.shape[0] / fs
    return feats
