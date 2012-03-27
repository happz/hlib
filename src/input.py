import types

import formencode
import formencode.api
import formencode.compound

from formencode import FancyValidator as Validator
from formencode.validators import NotEmpty, UnicodeString, MinLength, MaxLength, OneOf, FieldsMatch, Int, Email, StringBool, ConfirmType
from formencode.compound import Pipe, Any, All
from formencode.schema import Schema

import hlib
import hlib.error
import hlib.handlers

# pylint: disable-msg=F0401
import hruntime

class SchemaValidator(Schema):
  allow_extra_fields = False
  filter_extra_fields = True
  if_key_missing = None
  ignore_key_missing = False

def validator_factory(*validators):
  class PrivateValidator(Pipe):
    def __init__(self, *_args, **_kwargs):
      _kwargs['validators'] = list(validators)
      super(PrivateValidator, self).__init__(*_args, **_kwargs)

  return PrivateValidator

def validator_optional(validator):
  return Any(validator, ConfirmType(type = types.NoneType))

CommonString = validator_factory(NotEmpty(), UnicodeString())

Username = validator_factory(CommonString(), MinLength(2), MaxLength(30))
Password = validator_factory(CommonString(), MinLength(2), MaxLength(256))
Email    = validator_factory(CommonString(), Email())

def validate_by(schema = None):
  def _validate_by(fn):
    hlib.handlers.tag_fn(fn, 'validate_by', schema)
    return fn
  return _validate_by

def validate(schema = None, params = None, update_request = True):
  if not schema:
    schema = hlib.handlers.tag_fn_check(hruntime.request.handler, 'validate_by', None)

    if not schema:
      return

  # schema is just a class
  schema = schema()

  if not params:
    params = hruntime.request.params

  try:
    params = schema.to_python(params)

  except formencode.Invalid, e:
    if False:
      for k in ['args', 'error_dict', 'error_list', 'message', 'msg', 'state', 'unpack_errors', 'value']:
        print k
        print '  ',
        print unicode(getattr(e, k)).encode('ascii', 'replace')

    field_name = None
    field_error = None
    for field_name, field_error in e.error_dict.iteritems():
      break

    raise hlib.error.InvalidInputError(reply_status = 400, msg = field_error.msg, invalid_field = field_name)

  if update_request == True:
    hruntime.request.params.update(params)

  return params
