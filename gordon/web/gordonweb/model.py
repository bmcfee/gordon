# -*- coding: utf-8 -*-
"""This module contains the data model of the application."""


__all__ = ['Group', 'Permission', 'User', 'Visit', 'VisitIdentity']

from datetime import datetime

import pkg_resources
pkg_resources.require("SQLAlchemy>=0.4.3")

from turbogears.database import get_engine, metadata, session
# import the standard SQLAlchemy mapper
from sqlalchemy.orm import mapper
# To use the session-aware mapper use this import instead
# from turbogears.database import session_mapper as mapper
# import some basic SQLAlchemy classes for declaring the data model
# (see http://www.sqlalchemy.org/docs/05/ormtutorial.html)
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import relation
# import some datatypes for table columns from SQLAlchemy
# (see http://www.sqlalchemy.org/docs/05/reference/sqlalchemy/types.html for more)
from sqlalchemy import String, Unicode, Integer, DateTime
from sqlalchemy import func #for sum, count, etc
from turbogears import identity


# your data tables
# http://www.sqlalchemy.org/docs/05/metadata.html

# your_table = Table('yourtable', metadata,
#     Column('my_id', Integer, primary_key=True)
# )


# your model classes
# http://www.sqlalchemy.org/docs/05/ormtutorial.html#define-a-python-class-to-be-mapped

# class YourDataClass(object):
#     pass


# set up mappers between your data tables and classes
# http://www.sqlalchemy.orgg/docs/05/mappers.html

# mapper(YourDataClass, your_table)


# the identity schema

visits_table = Table('visit', metadata,
    Column('visit_key', String(40), primary_key=True),
    Column('created', DateTime, nullable=False, default=datetime.now),
    Column('expiry', DateTime)
)

visit_identity_table = Table('visit_identity', metadata,
    Column('visit_key', String(40), primary_key=True),
    Column('user_id', Integer, ForeignKey('tg_user.user_id'), index=True)
)

groups_table = Table('tg_group', metadata,
    Column('group_id', Integer, primary_key=True),
    Column('group_name', Unicode(16), unique=True, nullable=False),
    Column('display_name', Unicode(255)),
    Column('created', DateTime, default=datetime.now)
)

users_table = Table('tg_user', metadata,
    Column('user_id', Integer, primary_key=True),
    Column('user_name', Unicode(16), unique=True, nullable=False),
    Column('email_address', Unicode(255), unique=True),
    Column('display_name', Unicode(255)),
    Column('password', Unicode(40)),
    Column('created', DateTime, default=datetime.now)
)

permissions_table = Table('permission', metadata,
    Column('permission_id', Integer, primary_key=True),
    Column('permission_name', Unicode(16), unique=True, nullable=False),
    Column('description', Unicode(255))
)

user_group_table = Table('user_group', metadata,
    Column('user_id', Integer, ForeignKey('tg_user.user_id',
        onupdate='CASCADE', ondelete='CASCADE'), primary_key=True),
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
        onupdate='CASCADE', ondelete='CASCADE'), primary_key=True)
)

group_permission_table = Table('group_permission', metadata,
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
        onupdate='CASCADE', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permission.permission_id',
        onupdate='CASCADE', ondelete='CASCADE'), primary_key=True)
)


# the identity model

class Visit(object):
    """A visit to your site."""

    @classmethod
    def lookup_visit(cls, visit_key):
        """Look up Visit by given visit key."""
        return session.query(cls).get(visit_key)


class VisitIdentity(object):
    """A Visit that is linked to a User object."""

    @classmethod
    def by_visit_key(cls, visit_key):
        """Look up VisitIdentity by given visit key."""
        return session.query(cls).get(visit_key)


class Group(object):
    """An ultra-simple group definition."""

    def __repr__(self):
        return '<Group: name="%s", display_name="%s">' % (
            self.group_name, self.display_name)

    def __unicode__(self):
        return self.display_name or self.group_name

    @classmethod
    def by_group_name(cls, group_name):
        """Look up Group by given group name."""
        return session.query(cls).filter_by(group_name=group_name).first()
    by_name = by_group_name


class User(object):
    """Reasonably basic User definition.

    Probably would want additional attributes.

    """

    def __repr__(self):
        return '<User: name="%s", email="%s", display name="%s">' % (
            self.user_name, self.email_address, self.display_name)

    def __unicode__(self):
        return self.display_name or self.user_name

    @property
    def permissions(self):
        """Return all permissions os all groups the user belongs to."""
        p = set()
        for g in self.groups:
            p |= set(g.permissions)
        return p

    @classmethod
    def by_email_address(cls, email_address):
        """Look up User by given email address.

        This class method that can be used to search users based on their email
        addresses since it is unique.

        """
        return session.query(cls).filter_by(email_address=email_address).first()

    @classmethod
    def by_user_name(cls, user_name):
        """Look up User by given user name.

        This class method that permits to search users based on their
        user_name attribute.

        """
        return session.query(cls).filter_by(user_name=user_name).first()
    by_name = by_user_name

    def _set_password(self, password):
        """Run cleartext password through the hash algorithm before saving."""
        self._password = identity.encrypt_password(password)

    def _get_password(self):
        """Returns password."""
        return self._password

    password = property(_get_password, _set_password)


class Permission(object):
    """A relationship that determines what each Group can do."""

    def __repr__(self):
        return '<Permission: name="%s">' % self.permission_name

    def __unicode__(self):
        return self.permission_name

    @classmethod
    def by_permission_name(cls, permission_name):
        """Look up Permission by given permission name."""
        return session.query(cls).filter_by(permission_name=permission_name).first()
    by_name = by_permission_name


# set up mappers between identity tables and classes

mapper(Visit, visits_table)

mapper(VisitIdentity, visit_identity_table,
        properties=dict(users=relation(User, backref='visit_identity')))

mapper(User, users_table,
        properties=dict(_password=users_table.c.password))

mapper(Group, groups_table,
        properties=dict(users=relation(User,
                secondary=user_group_table, backref='groups')))

mapper(Permission, permissions_table,
        properties=dict(groups=relation(Group,
                secondary=group_permission_table, backref='permissions')))

# functions for populating the database

def bootstrap_model(clean=False, user=None):
    """Create all database tables and fill them with default data.

    This function is run by the 'bootstrap' function from the command module.
    By default it calls two functions to create all database tables for your
    model and optionally create a user.

    You can add more functions as you like to add more boostrap data to the
    database or enhance the functions below.

    If 'clean' is True, all tables defined by your model will be dropped before
    creating them again. If 'user' is not None, 'create_user' will be called
    with the given username.

    """
    create_tables(clean)
    if user:
        create_default_user(user)

def create_tables(drop_all=False):
    """Create all tables defined in the model in the database.

    Optionally drop existing tables before creating them.

    """
    get_engine()
    if drop_all:
        print "Dropping all database tables defined in model."
        metadata.drop_all()
    metadata.create_all()

    print "All database tables defined in model created."

def create_default_user(user_name, password=None):
    """Create a default user."""
    try:
        u = User.by_user_name(user_name)
    except:
        u = None
    if u:
        print "User '%s' already exists in database." % user_name
        return
    from getpass import getpass
    from sys import stdin
    while password is None:
        try:
            password = getpass("Enter password for user '%s': "
                % user_name.encode(stdin.encoding)).strip()
            password2 = getpass("Confirm password: ").strip()
            if password != password2:
                print "Passwords do not match."
            else:
                password = password.decode(stdin.encoding)
                break
        except (EOFError, KeyboardInterrupt):
            print "User creation cancelled."
            return
    u = User()
    u.user_name = user_name
    u.display_name = u"Default User"
    u.email_address = u"%s@nowhere.xyz" % user_name
    u.password = password
    session.add(u)
    session.flush()
    print "User '%s' created." % user_name
