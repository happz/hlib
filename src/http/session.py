__author__ = 'Milos Prchlik'
__copyright__ = 'Copyright 2010 - 2013, Milos Prchlik'
__contact__ = 'happz@happz.cz'
__license__ = 'http://www.php-suit.com/dpl'

import cPickle
import hashlib
import random
import string
import threading
import UserDict

import hlib.server
from hlib.stats import stats as STATS

# pylint: disable-msg=F0401
import hruntime  # @UnresolvedImport

__all__ = []

def gen_rand_string(l):
  chars = string.letters + string.digits
  return reduce(lambda s, i: s + random.choice(chars), range(l), '')

class Storage(UserDict.UserDict):
  def __init__(self, app, *args, **kwargs):
    UserDict.UserDict.__init__(self, *args, **kwargs)

    self.app = app

    self.lock = threading.RLock()

    self.sessions	= {}

    self.__online	= None
    self.__online_ctime	= 0

    self.stats_name = 'Sessions (%s)' % self.app.name

    with STATS:
      STATS.set(self.stats_name, {
      'Active': lambda s: ', '.join(self.online_users)
    })

  @property
  def online_users(self):
    with self.lock:
      if self.sessions == None:
        return []

      if hruntime.time - self.__online_ctime > 60 or self.__online == None:
        self.__online = []

        for session in self.sessions.values():
          if session.age < 300 and hasattr(session, 'authenticated') and hasattr(session, 'name') and session.name:
            self.__online.append(session.name)

        self.__online_ctime = hruntime.time

      return list(self.__online)

  def purge(self):
    with self.lock:
      rm = []

      for session in self.sessions.values():
        # pylint: disable-msg=E1101
        if session.age > self.app.config['sessions.time']:
          rm.append(session)

      for session in rm:
        session.destroy()

      self.__online = None

  def load(self, sid):
    return self[sid]

  def exists(self, sid):
    return sid in self

class MemoryStorage(Storage):
  def __contains__(self, name):
    with self.lock:
      return name in self.sessions

  def __getitem__(self, name):
    with self.lock:
      return self.sessions.get(name, None)

  def __setitem__(self, name, value):
    with self.lock:
      self.sessions[name] = value

  def __delitem__(self, name):
    with self.lock:
      if name in self.sessions:
        del self.sessions[name]

class FileStorage(Storage):
  def __init__(self, storage_file, *args, **kwargs):
    Storage.__init__(self, *args, **kwargs)

    self.storage_file = storage_file
    self.sessions = None

  def __open_session_file(self, mode = 'r', repeated = False):
    try:
      return open(self.storage_file, mode)
    except IOError, e:
      if repeated:
        raise e

      if hasattr(e, 'args') and len(e.args) >= 1 and e.args[0] == 2:
        with open(self.storage_file, 'w') as f:
          f.write(cPickle.dumps({}))
          f.close()

        return self.__open_session_file(repeated = True)

  def load_sessions(self):
    # pylint: disable-msg=E1101
    with self.__open_session_file() as f:
      self.sessions = cPickle.loads(f.read())

  def save_sessions(self):
    # pylint: disable-msg=E1101
    with self.__open_session_file(mode = 'w') as f:
      f.write(cPickle.dumps(self.sessions))

  def purge(self):
    with self.lock:
      Storage.purge(self)

      self.save_sessions()

  def __contains__(self, name):
    with self.lock:
      if self.sessions == None:
        self.load_sessions()

      return name in self.sessions

  def __getitem__(self, name):
    with self.lock:
      if self.sessions == None:
        self.load_sessions()

      return self.sessions.get(name, None)

  def __setitem__(self, name, value):
    with self.lock:
      if self.sessions == None:
        self.load_sessions()

      self.sessions[name] = value
      self.save_sessions()

  def __delitem__(self, name):
    with self.lock:
      if self.sessions == None:
        self.load_sessions()

      if name in self.sessions:
        del self.sessions[name]
        self.save_sessions()

class Session(object):
  def __init__(self, storage, time, ips):
    super(Session, self).__init__()

    self.storage	= storage
    self.code		= None
    self.sid		= None
    self.time		= time
    self.ip		= hlib.server.ips_to_str(ips)

    self.gen_sid()

  def __repr__(self):
    data = {
      'authenticated': self.authenticated if hasattr(self, 'authenticated') else None,
      'name': self.name if hasattr(self, 'name') else None,
      'tainted':		self.tainted if hasattr(self, 'tainted') else None
    }

    return 'session.Session(sid = \'%s\', time = \'%s\', ip = \'%s\', age = \'%s\', data = \'%s\')' % (self.sid, self.time, self.ip, hruntime.time - self.time, data)

  def __getattr__(self, name):
    if name == 'age':
      return hruntime.time - self.time

  def __getstate__(self):
    d = self.__dict__.copy()
    del d['storage']
    return d

  def __setstate__(self, d):
    self.__dict__ = d
    self.storage = hruntime.app.sessions

  @staticmethod
  def create():
    return Session(hruntime.app.sessions, hruntime.time, hruntime.request.ips)

  def gen_sid(self):
    self.code		= gen_rand_string(10)
    self.sid		= hashlib.md5('%s-%s-%s' % (hlib.server.ips_to_str(hruntime.request.ips), hruntime.time, self.code)).hexdigest()

  def check(self):
    if self.ip != hlib.server.ips_to_str(hruntime.request.ips):
      return False

    self.time = hruntime.time
    return True

  def refresh_sid(self):
    del self.storage[self.sid]
    self.gen_sid()

  def save(self):
    self.storage[self.sid] = self

  def destroy(self):
    del self.storage[self.sid]
