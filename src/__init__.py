"""
Basic classes for hlib functionality.

@type hlib.config.path:			C{string}
@var hlib.config.path:			Base path of this hlib instalation.
"""

__author__		= 'Milos Prchlik'
__copyright__		= 'Copyright 2010 - 2012, Milos Prchlik'
__contact__		= 'happz@happz.cz'
__license__		= 'http://www.php-suit.com/dpl'
__version__		= '3.0-rc1'

import os.path
import random
import sys
import time
import traceback
import types

import hlib.threadinglocal

__version__ = '3.0-rc1'
"""
Library version tag

@type:				C{string}
"""

class Config(object):
  """
  Simple object, inherited from basic L{object}, used for "object-tree" style of configuration variables, with L{hlib.config} as root.
  """

  def dump(self, prefix):
    """
    Print all non-internal attributes of this object. If attribute is L{Config} child dump its attributes too (viva la recursion!)

    @type prefix:		C{string}
    @param prefix:		Path of names (joined by dot) that leads to this object.
    """

    for n in dir(self):
      if n in ['__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'dump']:
        continue

      v = getattr(self, n)
      if v.__class__ == self.__class__:
        v.dump(prefix + '.' + n)
      else:
        print '%s.%s = "%s"' % (prefix, n, v)

config = Config()
"""
Root of hlib configuration variables.

@type:				hlib.Config
"""

# pylint: disable-msg=W0201
config.path = '/data/hlib/src/'
config.app_path = os.path.abspath(os.path.dirname(sys.argv[0]))

def url(path = None):
  return 'http://' + hruntime.request.base + path

# Thread-local/-global variables
_locals = hlib.threadinglocal.local()
"""
Thread-specific data storage
"""

class Runtime(types.ModuleType):
  """
  Module-like wrapper for thread-local runtime variables.
  """

  def reset_locals(self):
    for p in self.properties:
      setattr(_locals, p, None)

    _locals._stamp = None

  def __init__(self, *args):
    # pylint: disable-msg=W0233
    types.ModuleType.__init__(self, 'hlib.runtime')

    self.properties = args

    self.reset_locals()
    self.__init_done = False

  def __getattr__(self, name):
    if name in self.properties:
      return getattr(_locals, name)

    if name == 'time':
      # pylint: disable-msg=W0212
      if not hasattr(_locals, '_stamp') or _locals._stamp == None:
        _locals._stamp = int(time.time())

      return _locals._stamp

    if name == 'localtime':
      return time.localtime(self.time)

    if name == 'cache':
      return self.app.cache

  def __setattr__(self, name, value):
    if name == 'properties':
      types.ModuleType.__setattr__(self, name, value)
      return

    if name in self.properties:
      setattr(_locals, name, value)
      return

    if name == 'time':
      # pylint: disable-msg=W0212
      _locals._stamp = None
      return

    types.ModuleType.__setattr__(self, name, value)

sys.modules['hruntime'] = Runtime('__init_done', 'tid', 'stats', 'user', 'db', 'dbconn', 'dbroot', 'root', 'server', 'dont_commit', 'ui_form', 'app', 'request', 'response', 'session', 'localization')

# pylint: disable-msg=F0401
import hruntime

EVENTS = {}
"""
Allocated names of events. Key is event' name, value is corresponding class.
"""

def register_event(cls):
  """
  Register new event class.

  @type cls:			L{hlib.events.Event} class.
  @param cls:			Class responsible for handling this event.
  """

  # pylint: disable-msg=W0621
  import hlib.events
  EVENTS[hlib.events.ename(cls)] = cls
