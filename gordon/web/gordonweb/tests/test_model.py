# -*- coding: utf-8 -*-
"""Unit test cases for testing the application's model classes.

If your project uses a database, you should set up database tests similar to
what you see below.

Be sure to set the ``db_uri`` in the ``test.cfg`` configuration file in the
top-level directory of your project to an appropriate uri for your testing
database. SQLite is a good choice for testing, because you can use an in-memory
database which is very fast and the data in it has to be boot-strapped from
scratch every time, so the tests are independant of any pre-existing data.

You can also set the ``db_uri``directly in this test file but then be sure
to do this before you import your model, e.g.::

    from turbogears import testutil, database
    database.set_db_uri("sqlite:///:memory:")
    from gordonweb.model import YourModelClass, User, ...

See http://docs.turbogears.org/1.1/Testing#testing-your-model for more
information.

"""

from turbogears.testutil import DBTest
from turbogears.util import get_model

# import the User class defined in the model so we can use it here
try:
    from gordonweb.model import User, create_tables, create_default_user
except ImportError:
    import warnings
    warnings.warn("Identity model not found. Not running identity tests!")
    User = None

from turbogears.database import session
from sqlalchemy.exc import OperationalError

def _create_test_user():
    obj = User()
    obj.user_name = u"creosote"
    obj.email_address = u"spam@python.not"
    obj.display_name = u"Mr Creosote"
    obj.password = u"Wafer-thin Mint"
    # mark object as 'to be saved'
    session.add(obj)
    # flush marked object to database
    session.flush()
    return obj

class TestUser(DBTest):

    if User:
        def test_user_creation(self):
            """Object creation should set the name."""
            obj = _create_test_user()
            retrieved_user = User.by_email_address(u'spam@python.not')
            assert retrieved_user, \
                'User should have been found by email address'
            assert retrieved_user.user_name == u'creosote', \
                "User name should have been creosote, not '%s'" % retrieved_user.user_name
            assert obj.display_name == u"Mr Creosote"

class TestBootstrap(DBTest):

    def setUp(self):
        if not self.model:
            self.model = get_model()
            if not self.model:
                raise Exception("Unable to run database tests without a model")

    if User:
        def test_create_tables(self):
            """Test that model.create_tables correctly creates all database tables."""
            self.assertRaises(OperationalError, User.by_user_name, u'test')
            create_tables()
            assert _create_test_user()
            create_tables()
            assert User.by_user_name(u'creosote')
            create_tables(drop_all=True)
            user = User.by_user_name(u'creosote')
            assert user is None

        def test_create_default_user(self):
            "Test that the default user is created correctly"
            create_tables()
            create_default_user(u'creosote', u'secret')
            retrieved_user = User.by_email_address(u'%s@nowhere.xyz' % u'creosote')
            assert retrieved_user
            assert retrieved_user.user_name == u'creosote'
            assert retrieved_user.display_name == u'Default User'
            assert retrieved_user.password
