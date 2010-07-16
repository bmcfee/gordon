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

# Re-initialize the connection to the Matlab engine in case it got
# broken after it's initial import, which might have happened before
# importing this module.
import mlabwrap
reload(mlabwrap)

mlab.addpath(os.path.join(CURRDIR, 'coversongs'))


def extract_features(track, fctr=400, fsd=1.0, type=1):
    """Computes beat-synchronous chroma features.

    Returns a feature vector of beat-level chroma features (12 rows x
    n time step columns) using Dan Ellis' chrombeatftrs Matlab
    function (via the mlabwrap module, which is included with this
    feature extractor).

    Parameters
    ----------
    track : gordon Track instance
    fctr : float
        Center frequency (in Hz) for chromagram weighting.
    fsd : float
        Standard deviation (in octaves) for chromagram weighting.
    type : int
        Selects chroma calculation type; 1 (default) uses IF; 2 uses
        all FFT bins, 3 uses only local peaks (a bit like Emilia).
    """
    x,fs,svals = track.audio()

    feats,beats = mlab.chrombeatftrs(x.mean(1)[:,np.newaxis], fs, fctr, fsd,
                                     type, nout=2)
    songlen = x.shape[0] / fs
    return feats
