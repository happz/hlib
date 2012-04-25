import cPickle
import hashlib
import pprint
import random
# pylint: disable-msg=W0402
import string
import threading
import UserDict

import hlib
import hlib.event

# pylint: disable-msg=F0401
import hruntime

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

  @property
  def online_users(self):
    with self.lock:
      if hruntime.time - self.__online_ctime > 60:
        self.__online = []

        for session in self.sessions.itervalues():
          if session.time > hruntime.time - 300 and hasattr(session, 'authenticated') and hasattr(session, 'name'):
            self.__online.append(session.name)

      return self.__online

  def purge(self):
    with self.lock:
      rm = []

      for session in self.sessions.itervalues():
        # pylint: disable-msg=E1101
        if hruntime.time - session.time > self.app.config['sessions.time']:
          rm.append(session)

      for session in rm:
        session.destroy()

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

def gen_sid():
  # hashlib.md5 exists, no matter what pylint says...
  # pylint: disable-msg=E1101
  return hashlib.md5('%s-%s-%s' % (':'.join(hruntime.request.ip), hruntime.time, gen_rand_string(10))).hexdigest()

class Session(object):
  def __init__(self, storage, sid, time, ip):
    super(Session, self).__init__()

    self.storage	= storage
    self.sid		= sid
    self.time		= time
    self.ip		= ':'.join(ip)

  def __str__(self):
    return '%s - %s - %s (%s)' % (self.sid, self.time, self.ip, hruntime.time - self.time)

  def __getstate__(self):
    d = self.__dict__.copy()
    del d['storage']
    return d

  def __setstate__(self, d):
    self.__dict__ = d
    self.storage = hruntime.app.sessions

  @staticmethod
  def create():
    return hlib.http.session.Session(hruntime.app.sessions, gen_sid(), hruntime.time, hruntime.request.ip)

  def check(self):
    if self.ip != ':'.join(hruntime.request.ip):
      return False

    self.time = hruntime.time
    return True

  def refresh_sid(self):
    new_sid = gen_sid()

    del self.storage[self.sid]
    self.sid = new_sid

  def save(self):
    self.storage[self.sid] = self

  def destroy(self):
    del self.storage[self.sid]
