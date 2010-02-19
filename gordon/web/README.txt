gordonweb

This is a TurboGears (http://www.turbogears.org) project. It can be
started by running the start-gordonweb.py script.

To use this webserver, do these steps:

easy_install -U setuptools
easy_install TurboGears  (currently installs 1.1 by default)
easy_install SQLAlchemy  -- 0.5.6 works but generates some deprecation errors to be fixed
easy_install psycopg2
easy_install tgfastdata
easy_install SQLObject
easy_install RuleDispatch


In principle; 
easy_install TurboGears should do everything.  It may be worthwhile going to TurboGears2 for this reason.


Two init.d scripts are provided
