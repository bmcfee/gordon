import os
import sys

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
