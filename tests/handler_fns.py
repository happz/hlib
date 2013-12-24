from hlib.tests import *

import hlib.http
import hlib.input

def handler_nop1():
  pass

def handler_nop2():
  return None

def handler_echo_dict(ping = None):
  return {'pong': ping}

def handler_echo_json(ping = None):
  class Handler(hlib.api.ApiJSON):
    def __init__(self):
      super(Handler, self).__init__(['pong'])
      self.pong = ping
  return Handler()

def handler_undefined_var():
  a = b + c

def handler_int():
  return 1

def handler_exception_raised():
  raise RuntimeError('arbitrary string')

def handler_redirect():
  raise hlib.http.Redirect('/foo/')

class ValidateHandlerValidate(hlib.input.SchemaValidator):
  ping = hlib.input.validator_factory(hlib.input.NotEmpty, hlib.input.Int)

@hlib.input.validate_by(ValidateHandlerValidate)
def handler_validate(ping = None):
  ANY(ping)
  return {'pong': ping + 1, 'type': str(type(ping))}
