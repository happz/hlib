"""
JSON API support.
"""

__author__              = 'Milos Prchlik'
__copyright__           = 'Copyright 2010 - 2012, Milos Prchlik'
__contact__             = 'happz@happz.cz'
__license__             = 'http://www.php-suit.com/dpl'

import json
import sys
import traceback

import hlib.error
import hlib.handlers
import hlib.http
import hlib.log
import hlib.server

# pylint: disable-msg=F0401
import hruntime

PASSWORD_FIELD_FILTERS = [
  lambda s: s.startswith('password')
]

class JSONEncoder(json.JSONEncoder):
  """
  Our custom JSON encoder, able to encode L{hlib.api.ApiJSON} objects.

  @see:				http://docs.python.org/library/json.html#encoders-and-decoders
  """

  # pylint: disable-msg=E0202
  def default(self, o):
    return dict([[f, getattr(o, f)] for f in o.API_FIELDS]) if isinstance(o, ApiJSON) else super(JSONEncoder, self).default(o)

class ApiJSON(object):
  def __init__(self, fields):
    super(ApiJSON, self).__init__()

    # pylint: disable-msg=C0103
    self.API_FIELDS = []

    self.update(fields)

  def update(self, fields):
    self.API_FIELDS += fields

    for f in fields:
      setattr(self, f, None)

  def dump(self, o = None, **kwargs):
    hruntime.response.headers['Content-Type'] = 'application/json'

    return json.dumps(o or self, cls = JSONEncoder, **kwargs)

class Error(ApiJSON):
  def __init__(self, e):
    super(Error, self).__init__(['message', 'params'])

    self.message			= e.msg
    self.params				= e.params

class Form(ApiJSON):
  def __init__(self, orig_fields = False, remove_password = True, remove_fields = None, invalid_field = None, updated_fields = None):
    super(Form, self).__init__(['orig_fields', 'invalid_field', 'updated_fields'])

    if orig_fields:
      fields = hruntime.request.params.copy()
      fields_to_remove = []

      if remove_password:
        def _check_password_filters(s):
          for f in PASSWORD_FIELD_FILTERS:
            if f(s):
              return True
          return False

        # pylint: disable-msg=W0141
        fields_to_remove = filter(_check_password_filters, fields.keys())

      if remove_fields:
        fields_to_remove += remove_fields

      _fields = {}

      for k, v in fields.iteritems():
        if k in fields_to_remove:
          continue

        _fields[k] = v

      if len(_fields) > 0:
        self.orig_fields = _fields

    if invalid_field:
      self.invalid_field = invalid_field

    if updated_fields:
      self.updated_fields = updated_fields

class User(ApiJSON):
  def __init__(self, user):
    super(User, self).__init__(['name', 'is_online'])

    self.name		= user.name
    self.is_online	= user.is_online

class Reply(ApiJSON):
  def __init__(self, status, message = None, **kwargs):
    super(Reply, self).__init__(['status'])

    self.status         = status

    if message:
      self.update(['message'])
      self.message = message

    self.update(kwargs.keys())
    for k, v in kwargs.iteritems():
      setattr(self, k, v)

class Raw(ApiJSON):
  def __init__(self, data):
    super(Raw, self).__init__([])

    self.data = data

  def dump(self):
    return super(Raw, self).dump(o = self.data)

api = lambda f: hlib.handlers.tag_fn(f, 'api', True)
"""
Decorate handler as serving JSON API responses.

@type f:			C{Callable}
@param f:			C{Function} to decorate.
"""

def run_api_handler():
  try:
    hlib.input.validate()

    r = hruntime.request.handler(**hruntime.request.params)

    if r == None:
      r = Reply(200)

    return r.dump()

  except hlib.http.Redirect, e:
    raise e

  except Exception, e:
    hruntime.dont_commit = True

    e = hlib.error.error_from_exception(e)
    hlib.log.log_error(e)

    kwargs = e.args_for_reply()
    return Reply(e.reply_status, error = Error(e), **kwargs).dump()
