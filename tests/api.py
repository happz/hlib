from hlib.tests import *

import sys

import hlib.api
import hlib.engine

import handler_fns

import hruntime

class DummyServerHandler(object):
  def __init__(self):
    super(DummyServerHandler, self).__init__()
    self.server = None

class ApiIORegimeTests(TestCase):
  def test_redirect(self):
    hruntime.response = hlib.engine.Response()
    hruntime.response.status = None
    hruntime.response.output = None

    hlib.api.ApiIORegime.redirect('foo')

    EQ(hruntime.response.status, 200)
    JEQ(hruntime.response.output, {'status': 303, 'redirect': {'url': 'foo'}})

class HandlersTests(TestCase):
  def setup_hruntime(self):
    hruntime.db = hlib.database.DB('dummy db #1', None)
    hruntime.db.set_transaction_logging(enabled = False)
    hruntime.app = hlib.engine.Application('dummy app #1', None, hruntime.db, None)

  def reset_hruntime(self, handler, params):
    req = hruntime.request = hlib.engine.Request(0, None, None)
    res = hruntime.response = hlib.engine.Response()

    if 'Content-Type' in res.headers:
      del res.headers['Content-Type']

    req.handler = handler
    req.params = params

    return (req, res)

  def check_hruntime(self, expected_reply, real_reply):
    req = hruntime.request
    res = hruntime.response

    EQ(res.headers['Content-Type'], 'application/json')
    JEQ(expected_reply, real_reply)

  def test_handlers(self):
    self.setup_hruntime()

    self.reset_hruntime(handler_fns.handler_nop1, {})
    self.check_hruntime({'status': 200}, hlib.api.ApiIORegime.run_handler())

    self.reset_hruntime(handler_fns.handler_nop2, {})
    self.check_hruntime({'status': 200}, hlib.api.ApiIORegime.run_handler())

    self.reset_hruntime(handler_fns.handler_echo_dict, {'ping': 'foo'})
    self.check_hruntime({'pong': 'foo'}, hlib.api.ApiIORegime.run_handler())

    self.reset_hruntime(handler_fns.handler_echo_json, {'ping': 'foo'})
    self.check_hruntime({'pong': 'foo'}, hlib.api.ApiIORegime.run_handler())
    
    self.reset_hruntime(handler_fns.handler_undefined_var, {})
    self.check_hruntime({'status': 500, 'error': {'message': 'global name \'b\' is not defined', 'params': {}}}, hlib.api.ApiIORegime.run_handler())

    self.reset_hruntime(handler_fns.handler_int, {})
    self.check_hruntime({'status': 500, 'error': {'message': 'Invalid output produced by handler', 'params': {}}}, hlib.api.ApiIORegime.run_handler())

    self.reset_hruntime(handler_fns.handler_exception_raised, {})
    self.check_hruntime({'status': 500, 'error': {'message': 'arbitrary string', 'params': {}}}, hlib.api.ApiIORegime.run_handler())

    self.reset_hruntime(handler_fns.handler_redirect, {})
    e = EX(hlib.http.Redirect, hlib.api.ApiIORegime.run_handler)
    EQ('/foo/', e.location)

    self.reset_hruntime(handler_fns.handler_validate, {'ping': '1'})
    self.check_hruntime({'pong': 2, 'type': '<type \'int\'>'}, hlib.api.ApiIORegime.run_handler())

    self.reset_hruntime(handler_fns.handler_validate, {'ping': ''})
    self.check_hruntime({'status': 400, 'form': {'updated_fields': None, 'invalid_field': 'ping', 'orig_fields': {'ping': ''}}, 'error': {'message': 'Please enter a value', 'params': {}}},
                        hlib.api.ApiIORegime.run_handler())

    self.reset_hruntime(handler_fns.handler_validate, {'ping': 'string?'})
    self.check_hruntime({'status': 400, 'form': {'updated_fields': None, 'invalid_field': 'ping', 'orig_fields': {'ping': 'string?'}}, 'error': {'message': 'Please enter an integer value', 'params': {}}},
                        hlib.api.ApiIORegime.run_handler())
