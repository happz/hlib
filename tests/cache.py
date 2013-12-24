from hlib.tests import *

import hlib.cache
import hlib.datalayer
from hlib.stats import stats as STATS

class MockApp(object):
  def __init__(self, name, enabled = True):
    super(MockApp, self).__init__()

    self.name = name
    self.config = {
      'cache.enabled': enabled
    }

class CacheTests(hlib.tests.TestCase):
  _caches = {}
  _users = {}

  def cache(self, name, app_name = 'app #1', enabled = True):
    key = '%s-%s' % (app_name, name)
    caches = self.__class__._caches

    if key not in caches:
      caches[key] = hlib.cache.Cache(name, MockApp(app_name, enabled = enabled))

    return caches[key]

  def user(self, name):
    users = self.__class__._users

    if name not in users:
        users[name] = hlib.datalayer.User(name, 'password', 'email@email.cz')

    return users[name]

  def test_stats_name(self):
    c = self.cache('cache #1')

    EQ('Cache (app #1 - cache #1)', c.stats_name)

  def test_get_notcached(self):
    c = self.cache('cache #1')
    user = self.user('name')

    EQ(None, c.get(user, 'not-present'))
    EQ(None, c.get(user, 'not-present', default = None))
    EQ(1, c.get(user, 'not-present', default = 1))
    with STATS:
      EQ(0, STATS.get(c.stats_name, 'Hits'))
      EQ(3, STATS.get(c.stats_name, 'Misses'))

  def test_set(self):
    c = self.cache('cache #2')
    user = self.user('name')

    EQ(None, c.get(user, 'key1'))
    EQ(None, c.get(user, 'key2'))
    with STATS:
      EQ(0, STATS.get(c.stats_name, 'Hits'))
      EQ(2, STATS.get(c.stats_name, 'Misses'))

    c.set(user, 'key1', 'data')

    EQ('data', c.get(user, 'key1'))
    EQ(None, c.get(user, 'key2'))
    with STATS:
      EQ(1, STATS.get(c.stats_name, 'Inserts'))
      EQ(1, STATS.get(c.stats_name, 'Hits'))
      EQ(3, STATS.get(c.stats_name, 'Misses'))

  def test_remove(self):
    c = self.cache('cache #3')
    user = self.user('name')

    def assert_key(value, hits, misses):
      EQ(value, c.get(user, 'key'))
      with STATS:
        EQ(hits, STATS.get(c.stats_name, 'Hits'))
        EQ(misses, STATS.get(c.stats_name, 'Misses'))

    assert_key(None, 0, 1)
    c.set(user, 'key', 'data')
    assert_key('data', 1, 1)
    c.remove(user, 'key')
    assert_key(None, 1, 2)

  def test_remove_for_users(self):
    c = self.cache('cache #4')
    user1 = self.user('name1')
    user2 = self.user('name2')

    def assert_key(user, value, hits, misses):
      EQ(value, c.get(user, 'key'))
      with STATS:
        EQ(hits, STATS.get(c.stats_name, 'Hits'))
        EQ(misses, STATS.get(c.stats_name, 'Misses'))

    assert_key(user1, None, 0, 1)
    assert_key(user2, None, 0, 2)
    c.set(user1, 'key', 'data')
    assert_key(user1, 'data', 1, 2)
    assert_key(user2, None, 1, 3)
    c.set(user2, 'key', 'data')
    assert_key(user1, 'data', 2, 3)
    assert_key(user2, 'data', 3, 3)
    c.remove_for_users([user1, user2], 'key')
    assert_key(user1, None, 3, 4)
    assert_key(user2, None, 3, 5)

  def test_remove_for_all_users(self):
    c = self.cache('cache #5')
    user1 = self.user('name1')
    user2 = self.user('name2')

    def assert_key(user, value, hits, misses):
      EQ(value, c.get(user, 'key'))
      with STATS:
        EQ(hits, STATS.get(c.stats_name, 'Hits'))
        EQ(misses, STATS.get(c.stats_name, 'Misses'))

    assert_key(user1, None, 0, 1)
    assert_key(user2, None, 0, 2)
    c.set(user1, 'key', 'data')
    assert_key(user1, 'data', 1, 2)
    assert_key(user2, None, 1, 3)
    c.set(user2, 'key', 'data')
    assert_key(user1, 'data', 2, 3)
    assert_key(user2, 'data', 3, 3)
    c.remove_for_all_users('key')
    assert_key(user1, None, 3, 4)
    assert_key(user2, None, 3, 5)

  def test_caching_enabled(self):
    c = self.cache('cache #6', enabled = False)
    user = self.user('name')

    def assert_key(value, hits, misses):
      EQ(value, c.get(user, 'key'))
      with STATS:
        EQ(hits, STATS.get(c.stats_name, 'Hits'))
        EQ(misses, STATS.get(c.stats_name, 'Misses'))

    assert_key(None, 0, 0)
    c.set(user, 'key', 'data')
    assert_key(None, 0, 0)

  @SKIP
  def test_to_stats(self):
    pass
