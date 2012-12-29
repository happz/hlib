import threading

import hlib.stats

class Cache(object):
  def __init__(self, name, app):
    super(Cache, self).__init__()

    self.name		= name
    self.app		= app

    self.lock		= threading.RLock()
    self.objects	= {}

    self.stats_name		= 'Cache (%s - %s)' % (self.app.name, self.name)

    with hlib.stats.stats_lock:
      hlib.stats.stats[self.stats_name] = {
        'Total objects':	lambda s: sum([len(chain) for chain in self.objects.values()]),
        'Total chains':		lambda s: len(self.objects),
        'Total size':		lambda s: sum([sum([len(v) for v in chain.values()]) for chain in self.objects.values()]),
        'Hits':			0,
        'Misses':		0,
        'Inserts':		0,
        'Chains':		lambda s: self.to_stats()
      }

  def __inc_stats(self, name):
    with hlib.stats.stats_lock:
      hlib.stats.stats[self.stats_name][name] += 1

  def __chain_init(self, user):
    if user not in self.objects:
      self.objects[user] = {}

    return self.objects[user]

  def __check_caching_status(self, key):
    C = self.app.config

    if 'cache.enabled' not in C:
      return False

    if C['cache.enabled'] != True:
      return False

    ck = 'cache.dont_cache.' + key
    if ck not in C:
      return True

    if C[ck] != True:
      return True

    return False

  def get(self, user, key, default = None):
    if not self.__check_caching_status(key):
      return default

    with self.lock:
      chain = self.__chain_init(user)

      if key in chain:
        self.__inc_stats('Hits')

      else:
        self.__inc_stats('Misses')

      return chain.get(key, default = default)

  def set(self, user, key, value):
    if not self.__check_caching_status(key):
      return

    with self.lock:
      chain = self.__chain_init(user)

      chain[key] = value

    self.__inc_stats('Inserts')

  def test_and_set(self, user, key, callback, *args, **kwargs):
    if not self.__check_caching_status(key):
      return callback(*args, **kwargs)

    with self.lock:
      chain = self.__chain_init(user)

      if key not in chain:
        self.__inc_stats('Misses')
        chain[key] = callback(*args, **kwargs)
        self.__inc_stats('Inserts')

      else:
        self.__inc_stats('Hits')

      return chain[key]

  def remove(self, user, key):
    with self.lock:
      chain = self.__chain_init(user)

      if key in chain:
        del chain[key]

  def remove_for_users(self, users, key):
    with self.lock:
      for user in users:
        chain = self.__chain_init(user)

        if key in chain:
          del chain[key]

  def remove_for_all_users(self, key):
    with self.lock:
      for chain in self.objects.values():
        if key in chain:
          del chain[key]

  def to_stats(self):
    ret = {}

    with self.lock:
      for user, chain in self.objects.items():
        for key, value in chain.items():
          ret[user.name + ' - ' + key] = {'Type': str(type(value)).replace('<', '').replace('>', ''), 'Size': len(value)}

    return ret
