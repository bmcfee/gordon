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

try:
    mlab.sin(1)
except:
    # Re-initialize the broken connection to the Matlab engine.
    import mlabraw
    mlab._session = mlabraw.open()

mlab.addpath(os.path.join(CURRDIR, 'coversongs'))


def extract_features(track, fctr=400, fsd=1.0, type=1):
    """Computes beat-synchronous chroma features.

    Returns a feature vector of beat-level chroma features (12 rows x
    n time step columns) using Dan Ellis' chrombeatftrs Matlab
    function (via the mlabwrap module, which is included with this
    feature extractor).

    See http://labrosa.ee.columbia.edu/projects/coversongs
    for more details.

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
