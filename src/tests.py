import cookielib
import ConfigParser
import json
import random
import unittest
import urllib
import urllib2
import string
import sys
import types

__all__ = [
           'rand_string', 'cmp_json_dicts',
           'TestCase'
          ]

CONFIG_FILE = 'tests.conf'

CONFIG = ConfigParser.ConfigParser()
CONFIG.read(CONFIG_FILE)

def rand_string(length = 10):
  return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(length))

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
  def setUp(self):
    global CONFIG

    self.config = CONFIG
