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

def _dump_api_obj(o):
  r = {}

  for f in o.API_FIELDS:
    r[f] = getattr(o, f)

  return r

class JSONEncoder(json.JSONEncoder):
  # pylint: disable-msg=E0202
  def default(self, o):
    if not isinstance(o, ApiJSON):
      return super(JSONEncoder, self).default(o)

    return _dump_api_obj(o)

def api(f):
  hlib.handlers.tag_fn(f, 'api', True)
  return f

def run_api_handler():
  try:
    hlib.input.validate()

    r = hruntime.request.handler(**hruntime.request.params)

    if r == None:
      r = ApiReply(200)

    return r.dump()

  except hlib.http.Redirect, e:
    return ApiReply(200).dump()

  except Exception, e:
    hruntime.dont_commit = True

    if not isinstance(e, hlib.error.Error):
      e = hlib.error.ErrorByException(e)

    hlib.log.log_error(e)

    return ApiReply(e.reply_status, message = e.message, orig_fields = True, invalid_field = e.invalid_field).dump()

class ApiJSON(object):
  def __init__(self, fields, status = 200):
    super(ApiJSON, self).__init__()

    # pylint: disable-msg=C0103
    self.API_FIELDS = ['status']

    self.update(fields)

    self.status = status

  def update(self, fields):
    self.API_FIELDS += fields

    for f in fields:
      setattr(self, f, None)

  def dump(self, o = None, **kwargs):
    hruntime.response.headers['Content-Type'] = 'application/json'

    if o == None:
      o = self

    return json.dumps(o, cls = JSONEncoder, **kwargs)

class ApiFormInfo(ApiJSON):
  def __init__(self):
    super(ApiFormInfo, self).__init__(['orig_fields', 'invalid_field', 'updated_fields'])

class ApiUserInfo(ApiJSON):
  def __init__(self, user):
    super(ApiUserInfo, self).__init__(['name', 'is_online'])

    self.name		= user.name
    self.is_online	= user.is_online

class ApiReply(ApiJSON):
  def _setup_form_info(self):
    # pylint: disable-msg=E0203
    if not hasattr(self, 'form_info') or not self.form_info:
      self.update(['form_info'])
      # pylint: disable-msg=W0201
      self.form_info = ApiFormInfo()

  def __init__(self, status,
                     message          = None,
                     orig_fields      = False,
                     remove_password  = True,
                     remove_fields    = None,
                     invalid_field    = None,
                     updated_fields   = None,
                     **kwargs):
    super(ApiReply, self).__init__([])

    self.status         = status

    if message:
      self.message = message
      self.API_FIELDS.append('message')

    for k, v in kwargs.iteritems():
      setattr(self, k, v)
      self.API_FIELDS.append(k)

    if orig_fields:
      self._setup_form_info()

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

      self.form_info.orig_fields = _fields

    if invalid_field:
      self._setup_form_info()

      self.form_info.invalid_field = invalid_field

    if updated_fields:
      self._setup_form_info()

      self.form_info.updated_fields = updated_fields

class ApiRaw(ApiJSON):
  def __init__(self, data):
    super(ApiRaw, self).__init__([])

    self.data = data

  def dump(self):
    return super(ApiRaw, self).dump(o = self.data)
