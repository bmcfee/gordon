# -*- coding: utf-8 -*-
"""Unit test cases for testing the application's controller methods

See http://docs.turbogears.org/1.1/Testing#testing-your-controller for more
information.

"""
import unittest
import datetime
from turbogears import testutil
from gordonweb.controllers import Root
from gordonweb.model import User
from turbogears.database import session


class TestPages(testutil.TGTest):

    root = Root

    def test_method(self):
        """The index method should return a datetime.datetime called 'now'"""
        response = self.app.get('/')
        assert isinstance(response.raw['now'], datetime.datetime)

    def test_index_title(self):
        """"The index page should have the right title."""
        response = self.app.get('/')
        assert "<title>Welcome to TurboGears</title>" in response.body

    def test_login_title(self):
        """The login page should have the right title."""
        response = self.app.get('/login')
        assert "<title>Login</title>" in response
        assert "Please log in." in response
        assert "session cookies" not in response
        assert "credentials" not in response
        assert "not correct" not in response

    def test_login_errors(self):
        """The login page should display the right errors."""
        login = '/login?user_name=nobody&password=wrong&login=Login'
        response = self.app.get(login)
        assert "<title>Login</title>" in response
        assert "session cookies" in response
        cookie = ', '.join(map(str, response.cookies_set.values()))
        response = self.app.get(login, headers=dict(Cookie=cookie))
        assert "<title>Login</title>" in response
        assert "credentials" in response
        assert "not correct" in response

    def test_login_and_logout(self):
        """Login with correct credentials and then logout."""
        u = User()
        u.user_name = u"scott"
        u.password = u"tiger"
        u.display_name = u"Bruce Scott"
        u.email_address = u"scott@enterprise.com"
        session.add(u)
        session.flush()
        response = self.app.get('/')
        assert "<title>Welcome to TurboGears</title>" in response
        assert 'href="/login"' in response
        assert 'href="/logout"' not in response
        response = self.app.get('/login')
        assert "<title>Login</title>" in response
        assert 'Please log in.' in response
        cookie = ', '.join(map(str, response.cookies_set.values()))
        login = '/login?user_name=scott&password=tiger&login=Login'
        headers = dict(Cookie=cookie)
        response = self.app.get(login, headers=headers, status=302)
        location = response.headers['Location']
        response = self.app.get(location, headers=headers)
        assert "<title>Welcome to TurboGears</title>" in response
        assert "Welcome Bruce Scott" in response
        assert 'href="/login"' not in response
        assert 'href="/logout"' in response
        response = self.app.get('/', headers=headers)
        assert "<title>Welcome to TurboGears</title>" in response
        assert "Welcome Bruce Scott" in response
        assert 'href="/login"' not in response
        assert 'href="/logout"' in response
        response = self.app.get('/logout', headers=headers, status=302)
        location = response.headers['Location']
        response = self.app.get(location, headers=headers)
        assert "<title>Welcome to TurboGears</title>" in response
        assert 'href="/login"' in response
        assert 'href="/logout"' not in response
