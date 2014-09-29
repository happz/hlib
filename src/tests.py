__author__ = 'Milos Prchlik'
__copyright__ = 'Copyright 2010 - 2013, Milos Prchlik'
__contact__ = 'happz@happz.cz'
__license__ = 'http://www.php-suit.com/dpl'

import ConfigParser
import random
import unittest
import string
import sys
import types
import json
import time

__all__ = [
           'TestCase',
           'T', 'F', 'EQ', 'NEQ', 'EQ3', 'NONE', 'ANY', 'LEQ', 'JEQ', 'IN', 'NIN', 'EX', 'R', 'SKIP', 'Z', 'PAUSE',
          ]

def PAUSE(sec):
  time.sleep(sec)

def T(a, msg = None):
  msg = msg or ''
  assert a == True, msg

def F(a):
  assert a == False

def EQ(a, b):
  assert a == b

def Z(a):
  assert a == 0

def NEQ(a, b):
  assert a != b

def JEQ(a, b):
  if type(a) in types.StringTypes:
    a = json.loads(a)
  if type(b) in types.StringTypes:
    b = json.loads(b)

  def __check_dict(d1, d2, prefix):
    for k, v1 in d1.items():
      assert k in d2, 'key \'%s%s\' not present' % (prefix, k)

      v2 = d2[k]

      if type(v1) in types.StringTypes and type(v2) in types.StringTypes:
        pass

      else:
        assert type(v1) == type(v2), 'type mismatch for key \'%s\': got %s, expected %s' % (k, type(v2), type(v1))

        if type(v1) == types.DictType:
          __check_dict(v1, v2, prefix + '.' + k + '.')
          continue

      assert v1 == v2, 'reply[%s] = \'%s\', expected \'%s\'' % (k, unicode(v2).encode('ascii', 'replace'), v1)

  __check_dict(a, b, '')
  __check_dict(b, a, '')

def EQ3(a, b, c):
  EQ(a, b)
  EQ(b, c)
  EQ(c, a)

def NONE(a):
  EQ(a, None)

def ANY(a):
  NEQ(a, None)

def LEQ(seq, l):
  EQ(len(seq), l)

def IN(member, seq):
  assert member in seq

def NIN(member, seq):
  assert member not in seq

def EX(exc_cls, fn, *args, **kwargs):
  try:
    fn(*args, **kwargs)
  except exc_cls, e:
    return e
  else:
    assert False

from nose.tools import raises as R  # @UnusedImport
from nose.tools import nottest as SKIP  # @UnusedImport

def rand_string(length = 10):
  return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def cmp_json_dicts(reply, expect):
  def __check_dict(d1, d2, prefix):
    for k, v1 in d1.iteritems():
      assert k in d2, 'key \'%s.%s\' not present' % (prefix, k)

      v2 = d2[k]

      if type(v1) in types.StringTypes and type(v2) in types.StringTypes:
        pass

      else:
        assert type(v1) == type(v2), 'type mismatch for key \'%s\': got %s, expected %s' % (k, type(v2), type(v1))

        if type(v1) == types.DictType:
          __check_dict(v1, v2, prefix + '.' + k)
          continue

      assert v1 == v2, 'reply[%s] = \'%s\', expected \'%s\'' % (k, unicode(v2).encode('ascii', 'replace'), v1)

  try:
    __check_dict(expect, reply, '')
    __check_dict(reply, expect, '')

  except AssertionError, e:
    print >> sys.stderr, 'JSON reply: \'%s\'' % reply
    raise e

def patch_event_hooks(ename = None, callback = None):
  def __fake_call_nop(self, event):
    pass

  for event_name, hooks in hlib.events._HOOKS.items():
    if ename != None and ename != event_name:
      continue

    for hook in hooks:
      if callback:
        patched_call = types.MethodType(callback, hook, hook.__class__)
      else:
        patched_call = types.MethodType(__fake_call_nop, hook, hook.__class__)

      hook.__original_call = hook.__call__
      hook.__call__ = patched_call

def unpatch_event_hooks(ename = None):
  for event_name, hooks in hlib.events._HOOKS.items():
    if ename != None and ename != event_name:
      continue

    for hook in hooks:
      hook.__call__ = hook.__original_call

class DatabaseCache(object):
  _dbs = {}

  def __init__(self, config):
    super(DatabaseCache, self).__init__()

    self.config = config

  def db(self, name, addr):
    import hlib.database
    import os.path

    key = '%s-%s' % (name, addr)
    dbs = self.__class__._dbs

    if key not in dbs:
      addr = hlib.database.DBAddress(addr)
      addr.path = os.path.join(self.config.get('paths', 'tmpdir'), 'databases', addr.path)
      dbs[key] = hlib.database.DB(name, addr)
      dbs[key].set_transaction_logging(enabled = False)

    return dbs[key]

class TestCase(unittest.TestCase):
  @classmethod
  def setup_class(cls):
    pass

  @classmethod
  def teardown_class(cls):
    pass

  def __getattribute__(self, name):
    if name == 'config':
      from testconfig import config
      return config

    return super(TestCase, self).__getattribute__(name)
