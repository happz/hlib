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

hlib.config.sessions = hlib.Config()
hlib.config.sessions.storage = 'memory'
hlib.config.sessions.file = '/tmp/settlers-sessions.dat'
hlib.config.sessions.time = 2 * 86400

storage = None

def gen_rand_string(l):
  chars = string.letters + string.digits
  return reduce(lambda s, i: s + random.choice(chars), range(l), '')

class Storage(UserDict.UserDict):
  def __init__(self, *args, **kwargs):
    UserDict.UserDict.__init__(self, *args, **kwargs)

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
        if hruntime.time - session.time > hlib.config.sessions.time:
          rm.append(session)

      for session in rm:
        session.destroy()

class MemoryStorage(Storage):
  def __init__(self):
    Storage.__init__(self).__init__()

    self.sessions = {}

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
  def __init__(self):
    Storage.__init__(self)

    self.sessions = None

  def load_sessions(self):
    # pylint: disable-msg=E1101
    with open(hlib.config.sessions.file, 'r') as f:
      self.sessions = cPickle.loads(f.read())

  def save_sessions(self):
    # pylint: disable-msg=E1101
    with open(hlib.config.sessions.file, 'w') as f:
      f.write(cPickle.dumps(self.sessions))

  def __contains__(self, name):
    with self.lock:
      if self.sessions == None:
        self.load_sessions()

      return name in self.sessions

  def __getitem__(self, name):
    with self.lock:
      if self.sessions == None:
        self.sessions = self.load_sessions()

      return self.sessions.get(name, None)

  def __setitem__(self, name, value):
    with self.lock:
      if self.sessions == None:
        self.sessions = self.load_sessions()

      self.sessions[name] = value
      self.save_sessions()

  def __delitem__(self, name):
    with self.lock:
      if name in self.sessions:
        del self.sessions[name]
        self.save_sessions()

storage = None
storages = {
  'memory':	MemoryStorage,
  'file':	FileStorage
}

def gen_sid(req):
  # hashlib.md5 exists, no matter what pylint says...
  # pylint: disable-msg=E1101
  return hashlib.md5('%s-%s-%s' % (':'.join(req.ip), hruntime.time, gen_rand_string(10))).hexdigest()

class Session(object):
  def __init__(self, sid, time, ip):
    super(Session, self).__init__()

    self.sid		= sid
    self.time		= time
    self.ip		= ':'.join(ip)

  def __str__(self):
    return '%s - %s - %s (%s)' % (self.sid, self.time, self.ip, hruntime.time - self.time)

  @staticmethod
  def create(req):
    return hlib.http.session.Session(gen_sid(req), hruntime.time, req.ip)

  def check(self, req):
    if self.ip != ':'.join(req.ip):
      return False

    self.time = hruntime.time
    return True

  def refresh_sid(self, req):
    new_sid = gen_sid(req)

    del storage[self.sid]
    self.sid = new_sid

  def save(self):
    storage[self.sid] = self

  @staticmethod
  def load(sid):
    return storage[sid]

  @staticmethod
  def exists(sid):
    return sid in storage

  def destroy(self):
    del storage[self.sid]

# pylint: disable-msg=W0613
def __on_engine_started(e):
  # pylint: disable-msg=E1101
  hlib.http.session.storage = storages[hlib.config.sessions.storage]()

import hlib.event
hlib.event.Hook('engine.Started', 'session_storage', __on_engine_started, post = False)
