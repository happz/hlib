import os
import os.path
import transaction.interfaces
import shutil
import sys

from hlib.tests import *

import hlib.database
from hlib.stats import stats as STATS

class DBAddressTests(hlib.tests.TestCase):
  def test_address(self):
    addr = hlib.database.DBAddress('storage:substorage:user:password:host:path')

    EQ('storage', addr.storage)
    EQ('substorage', addr.substorage)
    EQ('user', addr.user)
    EQ('password', addr.password)
    EQ('host', addr.host)
    EQ('path', addr.path)

class DBTests(hlib.tests.TestCase):
  _dbs = {}

  @classmethod
  def setup_class(cls):
    super(DBTests, cls).setup_class()
    os.mkdir(os.path.join(cls.config.get('paths', 'tmpdir'), 'databases'))

  @classmethod
  def teardown_class(cls):
    super(DBTests, cls).teardown_class()
    shutil.rmtree(os.path.join(cls.config.get('paths', 'tmpdir'), 'databases'))

  def db(self, name, addr):
    key = '%s-%s' % (name, addr)
    dbs = self.__class__._dbs

    if key not in dbs:
      addr = hlib.database.DBAddress(addr)
      addr.path = os.path.join(self.config.get('paths', 'tmpdir'), 'databases', addr.path)
      dbs[key] = hlib.database.DB(name, addr)
      dbs[key].set_transaction_logging(enabled = False)

    return dbs[key]

  def test_imports(self):
    from hlib.database import TreeMapping  # @UnusedImport
    from hlib.database import StringMapping
    from hlib.database import ObjectMapping
    from hlib.database import SimpleList  # @UnusedImport
    from hlib.database import SimpleMapping  # @UnusedImport
    from hlib.database import Length  # @UnusedImport

  def test_create_db(self):
    D = self.db('db - create', 'FileStorage:::::db-create')
    D.open()
    D.connect()
    D.close()

  def test_storage_sanity(self):
    D = self.db('db - storage sanity', 'FileStorage:::::db-storage-sanity')

    D.open()
    connection, root = D.connect()
    D.start_transaction()
    root['key1'] = 'data1'
    D.commit()
    D.close()

    D.open()
    connection, root = D.connect()
    IN('key1', root)
    EQ('data1', root['key1'])
    D.start_transaction()
    root['key2'] = 'data2'
    D.commit()
    D.close()
    
    D.open()
    connection, root = D.connect()
    IN('key1', root)
    EQ('data1', root['key1'])
    IN('key2', root)
    EQ('data2', root['key2'])
    D.close()

  def test_rollback(self):
    D = self.db('db - rollback', 'FileStorage:::::db-rollback')

    D.open()
    connection, root = D.connect()
    D.start_transaction()
    root['key1'] = 'data1'
    D.commit()
    D.close()

    D.open()
    connection, root = D.connect()
    IN('key1', root)
    EQ('data1', root['key1'])
    D.start_transaction()
    root['key2'] = 'data2'
    D.rollback()
    D.close()

    D.open()
    connection, root = D.connect()
    IN('key1', root)
    EQ('data1', root['key1'])
    NIN('key2', root)
    D.close()

  @R(transaction.interfaces.DoomedTransaction)
  def test_doom(self):
    D = self.db('db - doom', 'FileStorage:::::db-doom')

    D.open()
    connection, root = D.connect()
    D.start_transaction()
    root['key1'] = 'data1'
    D.commit()
    D.close()

    D.open()
    connection, root = D.connect()
    IN('key1', root)
    EQ('data1', root['key1'])
    D.start_transaction()
    root['key2'] = 'data2'
    D.doom()
    root['key3'] = 'data3'

    # DoomedTransaction exception should be raised
    D.commit()

  def test_stats(self):
    D = self.db('db - stats', 'FileStorage:::::db-stats')

    D.open()
    connection, root = D.connect()
    D.start_transaction()

    for i in range(0, 10):
      root['key%i' % i] = 'data%i' % i

    D.commit()
    D.close()

    D.open()
    connection, root = D.connect()
    D.start_transaction()

    for i in range(0, 10):
      _ = root['key%i' % i]

    D.commit()

    D.update_stats()

    with STATS:
      stats_snapshot = STATS.snapshot()

    import pprint
    pprint.pprint(stats_snapshot)
    db_key = 'Database (db - stats)'

    IN(db_key, stats_snapshot)
    for e in ['Caches', 'Connections', 'Loads', 'Stores']:
      IN(e, stats_snapshot[db_key])
    LEQ(stats_snapshot[db_key]['Caches'], 1)
    LEQ(stats_snapshot[db_key]['Connections'], 1)

  def test_lists(self):
    D = self.db('db - lists', 'FileStorage:::::db-lists')

    D.open()
    connection, root = D.connect()
    D.start_transaction()
    L = hlib.database.SimpleList()
    L.append(0)
    L.append(1)
    LEQ(L, 2)
    root['L'] = L
    D.commit()
    D.start_transaction()
    L.append(2)
    D.commit()
    D.close()

    D.open()
    connection, root = D.connect()
    for i in range(0, 3):
      IN(i, root['L'])
    LEQ(root['L'], 3)
    D.rollback()
    D.close()
    
class DummyIndexable(object):
  def __init__(self):
    super(DummyIndexable, self).__init__()
    self.id = None

class IndexedMappingTests(hlib.tests.TestCase):
  def test_sanity(self):
    im = hlib.database.IndexedMapping()

    o1 = DummyIndexable()
    o2 = DummyIndexable()
    o3 = DummyIndexable()

    def assert_ids(id1, id2, id3):
      EQ(id1, o1.id)
      EQ(id2, o2.id)
      EQ(id3, o3.id)

    def assert_im(l):
      LEQ(im, l)
      LEQ(im.keys(), l)
      LEQ(im.values(), l)

    assert_ids(None, None, None)
    assert_im(0)

    im.push(o1)

    assert_ids(0, None, None)
    assert_im(1)

    im.push(o2)

    assert_ids(0, 1, None)
    assert_im(2)

    im.push(o3)

    assert_ids(0, 1, 2)
    assert_im(3)

    im.pop()

    assert_ids(0, 1, 2)
    assert_im(2)

    im.push(o3)

    assert_ids(0, 1, 2)
    assert_im(3)

    o = im.last()

    assert_ids(0, 1, 2)
    assert_im(3)

    EQ(2, o.id)

class DummyDBObject(hlib.database.DBObject):
  def __init__(self):
    hlib.database.DBObject.__init__(self)

    self._foo = None
    self._bar = None

  def __getattr__(self, name):
    if name == 'foo':
      return self._foo
    if name == 'bar':
      return self._bar

    return hlib.database.DBObject.__getattr__(self, name)

  def __setattr__(self, name, value):
    if name == 'foo':
      self._foo = value
    elif name == 'bar':
      self._bar = value
    else:
      hlib.database.DBObject.__setattr__(self, name, value)

class DBObjectTests(hlib.tests.TestCase):
  def test_attr_access(self):
    a = DummyDBObject()

    EQ3(a.foo, a._foo, None)
    EQ3(a.bar, a._bar, None)
    a.foo = 1
    EQ3(a.foo, a._foo, 1)
    EQ3(a.bar, a._bar, None)
    a.bar = 2
    EQ3(a.foo, a._foo, 1)
    EQ3(a.bar, a._bar, 2)

  @R(AttributeError)
  def test_unknown_attr(self):
    a = DummyDBObject()
    _ = a.baz

  @SKIP
  def test_conflicts(self):
    pass
