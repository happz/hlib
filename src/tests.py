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

__all__ = [
           'TestCase',
           'T', 'F', 'EQ', 'NEQ', 'EQ3', 'NONE', 'ANY', 'LEQ', 'JEQ', 'IN', 'NIN', 'EX', 'R', 'SKIP', 'Z'
          ]

def T(a):
  assert a == True

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

CONFIG_FILE = 'tests.conf'

CONFIG = ConfigParser.ConfigParser()
CONFIG.read(CONFIG_FILE)

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

class TestCase(unittest.TestCase):
  @classmethod
  def setup_class(cls):
    global CONFIG

    cls.config = CONFIG

  @classmethod
  def teardown_class(cls):
    pass
