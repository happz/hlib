"""
System statistics
"""

__author__              = 'Milos Prchlik'
__copyright__           = 'Copyright 2010 - 2012, Milos Prchlik'
__contact__             = 'happz@happz.cz'
__license__             = 'http://www.php-suit.com/dpl'

import pprint
import threading
import time
import types

# pylint: disable-msg=F0401
import hruntime

stats = {
}

stats_fmt = {
  'Engine':			{
    'Start time':		'%i',
    'Current time':		'%i',
  }
}

stats_lock = threading.RLock()

def init_namespace(name, content):
  with stats_lock:
    stats[name] = content

def swap_namespace(name, content):
  with stats_lock:
    stats[name] = content

def snapshot(d_in):
  with stats_lock:
    d_out = {}

    for k, v in list(d_in.items()):
      if k == '__fmt__':
        pass

      elif isinstance(v, dict):
        v = snapshot(v)

      elif isinstance(v, (list, tuple)):
        v = [snapshot(r) for r in v]

      elif hasattr(v, '__call__'):
        v = v(d_in)

      d_out[k] = v

    return d_out

def iter_collection(collection):
  if type(collection) == types.DictType:
    keys = collection.keys()
  else:
    keys = range(0, len(collection))

  for k in keys:
    d = {'ID': k}
    d.update(collection[k])
    yield d
