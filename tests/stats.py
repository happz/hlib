from hlib.tests import *

from hlib.stats import stats as STATS

class StatsTests(TestCase):
  def test_sanity(self):
    with STATS:
      STATS.set('key1', {
        'foo': 1,
        'bar': 2,
        'baz': {
          'key1_foo': 7
        }
      })

      EQ(STATS.get('key1', 'foo'), 1)
      EQ(STATS.get('key1', 'bar'), 2)
      EQ(STATS.get('key1', 'baz', 'key1_foo'), 7)

      STATS.inc('key1', 'foo')
      STATS.add('key1', 'bar', 2)
      STATS.inc('key1', 'baz', 'key1_foo')

      EQ(STATS.get('key1', 'foo'), 2)
      EQ(STATS.get('key1', 'bar'), 4)
      EQ(STATS.get('key1', 'baz', 'key1_foo'), 8)
