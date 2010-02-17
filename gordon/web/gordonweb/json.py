# -*- coding: utf-8 -*-
"""This module contains rules to map data model objects into JSON."""

# This file can be safely deleted from your project if do not use JSON
# controllers.

# A JSON-based API(view) for your app.
# Most rules would look like:
# @jsonify.when("isinstance(obj, YourClass)")
# def jsonify_yourclass(obj):
#     return [obj.val1, obj.val2]
# @jsonify can convert your objects to following types:
# lists, dicts, numbers and strings

from turbojson.jsonify import jsonify
from turbojson.jsonify import jsonify_saobject

from gordonweb.model import User, Group, Permission

@jsonify.when('isinstance(obj, Group)')
def jsonify_group(obj):
    result = jsonify_saobject(obj)
    result["users"] = [u.user_name for u in obj.users]
    result["permissions"] = [p.permission_name for p in obj.permissions]
    return result

@jsonify.when('isinstance(obj, User)')
def jsonify_user(obj):
    result = jsonify_saobject(obj)
    try: del result['password']
    except KeyError: pass
    try: del result['_password']
    except KeyError: pass
    result["groups"] = [g.group_name for g in obj.groups]
    result["permissions"] = [p.permission_name for p in obj.permissions]
    return result

@jsonify.when('isinstance(obj, Permission)')
def jsonify_permission(obj):
    result = jsonify_saobject(obj)
    result["groups"] = [g.group_name for g in obj.groups]
    return result
