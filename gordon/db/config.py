"""Local configuration for gordon database."""
# CREATED:2013-12-20 22:06:03 by Brian McFee <brm2132@columbia.edu>
# redo this using ini files
# pull ini path from an environment variable
#
#   ini path priority:
#       os.environ['GORDON_INI']
#       /etc/gordon.ini
#       /usr/etc/gordon.ini
#       /usr/local/etc/gordon.ini


# keys:
#   debug
#   DEF_GORDON_DIR
#   DEF_GORDON_DIR_ON_WEBSERVER
#   DEF_DBDRIVER
#   DEF_DBHOST
#   DEF_DBNAME
#   DEF_DBSUPERUSER
#   DEF_DBUSER
#   DEF_DBPASS
#   DEF_DBFILE
#
import logging, sys, os, ConfigParser

module  = sys.modules[__name__]
log     = logging.getLogger('gordon')

def load_config(ini_file):

    parser      = ConfigParser.SafeConfigParser()

    parser.read(ini_file)
    
    config = {}
    for k, v in dict(parser.items('gordon')).iteritems():
        config[k.upper()] = v

    keys = [    'DEBUG', 
                'DEF_GORDON_DIR', 
                'DEF_GORDON_DIR_ON_WEBSERVER',
                'DEF_DBDRIVER',
                'DEF_DBHOST',
                'DEF_DBNAME',
                'DEF_DBSUPERUSER',
                'DEF_DBUSER',
                'DEF_DBPASS',
                'DEF_DBFILE']

    for k in keys:
        if k in config:
            globals()[k] = config[k]

def init():
    # Search for the ini files
    log.addHandler(logging.StreamHandler(sys.stdout))

    ini_files = ['/etc/gordon.ini', '/usr/etc/gordon.ini', '/usr/local/etc/gordon.ini']

    if 'GORDON_INI' in os.environ:
        ini_files = [os.environ['GORDON_INI']]

    for f in ini_files:
        if os.path.exists(f):
            log.log(logging.INFO, 'Loading ini file from %s', f)
            load_config(f)
            _g = globals()
            if 'DEBUG' in _g and _g['DEBUG']:
                log.setLevel(logging.DEBUG)
            return

    log.log(logging.ERROR, 'No valid ini file found in %s', repr(ini_files))
    raise

init()
