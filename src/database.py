import random
import time
import types
import sys
import traceback

import ZODB
import ZODB.DB
import ZODB.FileStorage
import ZODB.POSException
import transaction
import BTrees
import persistent
import ZODB.ActivityMonitor

import hlib
import hlib.error
import hlib.log

from hlib.stats import stats, stats_lock

class CommitFailedError(hlib.error.BaseError):
  pass

class Storage(object):
  # pylint: disable-msg=W0613
  @staticmethod
  def open(address):
    return None

class Storage_MySQL(Storage):
  @staticmethod
  def open(address):
    try:
      import relstorage.adapters.mysql
      adapter = relstorage.adapters.mysql.MySQLAdapter(host = address.host,
                                                       user = address.user,
                                                       passwd = address.password,
                                                       db     = address.path)

      import relstorage.storage
      return relstorage.storage.RelStorage(adapter)

    except Exception, e:
      raise hlib.error.BaseError(msg = e.args[1], exception = e, exc_info = sys.exc_info())

class Storage_File(Storage):
  @staticmethod
  def open(address):
    return ZODB.FileStorage.FileStorage(address.path)

storage_classes = {
  'RelStorage': Storage_MySQL,
  'FileStorage': Storage_File
}

class DBAddress(object):
  _fields = {
    'storage':    0,
    'substorage': 1,
    'user':       2,
    'password':   3,
    'host':       4,
    'path':       5
  }

  def __init__(self, line):
    super(DBAddress, self).__init__()

    self.fields = line.split(':')

  def __getattr__(self, name):
    if name in self._fields.keys():
      return self.fields[self._fields[name]]

class DB(object):
  def __init__(self, name, address, **kwargs):
    super(DB, self).__init__()

    self.name		= name
    self.address	= address
    self.db		= None
    self.root		= None

    self.kwargs		= kwargs

    self.stats_name	= 'Database (%s)' % self.name

    # pylint: disable-msg=W0621
    import hlib.stats
    hlib.stats.init_namespace(self.stats_name, {
      'Loads':		0,
      'Stores':		0,
      'Commits':		0,
      'Rollbacks':		0,
      'Connections':	{},
      'Caches':		{}
    })

    import hlib.event
    hlib.event.Hook('engine.ThreadFinished', 'hlib.database.DB(%s)' % self.name, self.on_thread_finished)
    hlib.event.Hook('engine.RequestFinished', 'hlib.database.DB(%s)' % self.name, self.on_request_finished)

  def on_thread_finished(self, _):
    self.update_stats()

  def on_request_finished(self, _):
    self.update_stats()

  def open(self):
    storage = storage_classes[self.address.storage].open(self.address)
    self.db = ZODB.DB(storage, **self.kwargs)

    self.db.setActivityMonitor(ZODB.ActivityMonitor.ActivityMonitor())

  def connect(self):
    connection = self.db.open()
    self.root = connection.root()

    return (connection, self.root)

  def start_transaction(self):
    transaction.begin()

  def commit(self):
    try:
      with stats_lock:
        stats[self.stats_name]['Commits'] += 1

      transaction.commit()

    except ZODB.POSException.ConflictError, e:
      with stats_lock:
        stats[self.stats_name]['Failed commits'] += 1

      print >> sys.stderr, 'Conflict Error:'
      print >> sys.stderr, '  class_name: ' + str(e.class_name)
      print >> sys.stderr, '  msg: ' + str(e.message)
      print >> sys.stderr, '  data: ' + str(e.args)
      print >> sys.stderr, '  info: ' + str(e.serials)

      print traceback.format_exc()
      print e

      return False

    return True

  def rollback(self):
    with stats_lock:
      stats[self.stats_name]['Rollbacks'] += 1

    transaction.abort()

  def pack(self):
    self.db.pack()

  def update_stats(self):
    data = self.db.getActivityMonitor().getActivityAnalysis(divisions = 1)[0]

    with stats_lock:
      d = stats[self.stats_name]

      d['Loads']		= data['loads']
      d['Stores']		= data['stores']

      d['Connections']		= {}
      d['Caches']		= {}

      i = 0
      for data in self.db.connectionDebugInfo():
        d['Connections'][i] = {
          'Opened':		data['opened'],
          'Info':		data['info'],
          'Before':		data['before']
        }

      for data in self.db.cacheDetailSize():
        d['Caches'][data['connection']] = {
          'Non-ghost size':	data['ngsize'],
          'Size':		data['size']
        }

def abstract_method(obj = None):
  """
  Wrapper for unimplemented functions.

  @param obj:			Class object in which calling method was unimplemented.
  @raise UnimplementedError:	Every time
  """

  raise hlib.error.UnimplementedError(obj)

class DBObject(persistent.Persistent):
  def __init__(self, *args, **kwargs):
    persistent.Persistent.__init__(self, *args, **kwargs)

  def __getattr__(self, name):
    raise AttributeError(name)

class IndexedMapping(DBObject):
  def __init__(self, first_key = None, *args, **kwargs):
    DBObject.__init__(self, *args, **kwargs)

    self.data = BTrees.IOBTree.IOBTree()

    if first_key == None:
      self.first_key = 0

    else:
      self.first_key = first_key

  def __len__(self):
    return len(self.data)

  def __iter__(self):
    return iter(self.data)

  def __setitem__(self, key, value):
    self.data[key] = value

  def __getitem__(self, key):
    return self.data[key]

  def __delitem__(self, key):
    del self.data[key]

  def __contains__(self, key):
    return key in self.data

  def iteritems(self):
    return self.data.iteritems()

  def iterkeys(self):
    return self.data.iterkeys()

  def itervalues(self):
    return self.data.itervalues()

  def keys(self, *args, **kwargs):
    return self.data.keys(*args, **kwargs)

  def values(self, *args, **kwargs):
    return self.data.values(*args, **kwargs)

  def items(self, *args, **kwargs):
    return self.data.items(*args, **kwargs)

  def push(self, o):
    if len(self.data) == 0:
      i = self.first_key

    else:
      i = self.data.maxKey() + 1

    o.id = i
    self.data[i] = o

  def pop(self):
    i = self.data.maxKey()
    del self.data[i]

  def last(self):
    return self.data[self.data.maxKey()]

from BTrees.IOBTree import IOBTree as TreeMapping
from BTrees.OOBTree import OOBTree as StringMapping
ObjectMapping = StringMapping

from persistent.list import PersistentList as SimpleList
from persistent.mapping import PersistentMapping as SimpleMapping

from BTrees.Length import Length
