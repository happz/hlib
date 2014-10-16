import collections
import cPickle
import os
import os.path
import tempfile

import hlib.http.session

from tests import *

import hruntime

class CachedMemoryStorage_save_sessions(TestCase):
  @classmethod
  def setup_class(cls):
    handle, storage_file = tempfile.mkstemp()
    os.close(handle)
    os.unlink(storage_file)

    cls.storage_file = storage_file

    class MockApp(object):
      pass

    class MockRequest(object):
      pass

    app = MockApp()
    app.name = 'mock app'
    app.sessions = None

    req = MockRequest()
    req.ips = ['127.0.0.1']

    hruntime.app = app
    hruntime.request = req

    cls.storage = storage = hlib.http.session.CachedMemoryStorage(storage_file, app)
    app.sessions = storage

    NONE('Session list is not None but {actual}', storage.sessions)

    storage['Mock User #1'] = hlib.http.session.Session(storage, 0, '127.0.0.1')

    LEQ('One session expected but {actual} found',
        storage.sessions, 1)

    cls.orig_cpickle_dumps = cPickle.dumps

  def __test_save(self, dumper):
    if os.path.exists(self.__class__.storage_file):
      os.unlink(self.__class__.storage_file)

    cPickle.dumps = dumper

    self.__class__.storage.save_sessions()

    with open(self.__class__.storage_file, 'r') as f:
      storage_copy = cPickle.loads(f.read())

    LEQ('One saved session expected but {actual} found', storage_copy, 1)

  def test_common_scenario(self):
    def __dumps(*args, **kwargs):
      return self.__class__.orig_cpickle_dumps(*args, **kwargs)

    self.__test_save(__dumps)

  def test_dictionary_change(self):
    def __dumps(*args, **kwargs):
      __dumps.counter = 0
      if __dumps.counter == 5:
        raise RuntimeError('dictionary changed size during iteration')

      return self.__class__.orig_cpickle_dumps(*args, **kwargs)

    __dumps.counter = 0

    self.__test_save(__dumps)

  @R(RuntimeError)
  def test_runtime_error(self):
    def __dumps(*args, **kwargs):
      raise RuntimeError('Some strange runtime error')

    self.__test_save(__dumps)

  @R(Exception)
  def test_generic_exception(self):
    def __dumps(*args, **kwargs):
      raise Exception('Generic exception')

    self.__test_save(__dumps)
