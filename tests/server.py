from hlib.tests import *

import functools
import threading
import time

import hlib.events
import hlib.events.engine
import hlib.server
from hlib.stats import stats as STATS

import hruntime

class Log(object):
  def __init__(self):
    super(Log, self).__init__()

    self.lock = threading.Lock()
    self.records = []

  def log(self, request):
    with self.lock:
      self.records.append(request)

class MockRequest(object):
  def __init__(self):
    super(MockRequest, self).__init__()

    self.server = None
    self.ctime = int(time.time())

    self.read_bytes = 0
    self.written_bytes = 0

class MockServer(object):
  def __init__(self, name):
    super(MockServer, self).__init__()

    self.name = name
    self.pool = None
    self.log = Log()

  def process_request_thread(self, pool):
    hlib.events.trigger('engine.ThreadStarted', None, server = self)

    while True:
      request = pool.get_request()
      hruntime.request = MockRequest()

      self.log.log(request)

      if request.request_type == hlib.server.ThreadRequest.TYPE_QUIT:
        break

      hlib.events.trigger('engine.RequestConnected', None)
      hlib.events.trigger('engine.RequestFinished', None)

    hlib.events.trigger('engine.ThreadFinished', None, server = self)
    pool.remove_thread()

class ThreadPoolTests(TestCase):
  _pools = {}

  def pool(self, name, limit):
    key = '%s-%i' % (name, limit)
    pools = self.__class__._pools

    if key not in pools:
      pools[key] = hlib.server.ThreadPool(MockServer(name), limit = limit)
      pools[key].server.pool = pools[key]
      pools[key].start()

    return pools[key]

  @SKIP
  def test_sanity(self):
    pool = self.pool('server #1', 5)

    pool_stats_get = functools.partial(STATS.get, pool.stats_name)

    with STATS:
      Z(pool_stats_get('Total threads started'))
      Z(pool_stats_get('Total threads finished'))
      Z(len(pool_stats_get('Threads')))

    pool.add_request(hlib.server.ThreadRequest(hlib.server.ThreadRequest.TYPE_REQUEST, request = 'dummy request', client_address = 'client address'))

    time.sleep(10)

    with STATS:
      EQ(pool_stats_get('Total threads started'), 1)
      Z(pool_stats_get('Total threads finished'))
      EQ(len(pool_stats_get('Threads')), 1)
      EQ(pool_stats_get('Threads', 'worker-1', 'Total requests'), 1)

    pool.stop()
    #time.sleep(10)
    print pool_stats_get()

    assert False
