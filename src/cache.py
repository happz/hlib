import threading

class Cache(object):
  def __init__(self, name, app):
    super(Cache, self).__init__()

    self.name		= name
    self.app		= app

    self.lock		= threading.RLock()
    self.objects	= {}

    from hlib.stats import stats as sd
    from hlib.stats import stats_lock as sl

    with sl:
      sd['Cache (%s - %s)' % (self.app.name, self.name)] = {
        'Total objects':	lambda s: sum([len(chain) for chain in self.objects.values()]),
        'Total chains':		lambda s: len(self.objects),
        'Total size':		lambda s: sum([sum([len(v) for v in chain.values()]) for chain in self.objects.values()]),
        'Hits':			0,
        'Misses':		0,
        'Inserts':		0,
        'Chains':		lambda s: self.to_stats()
      }

  def __chain_init(self, user):
    if user not in self.objects:
      self.objects[user] = {}

    return self.objects[user]

  def get(self, user, key, default = None):
    if not self.app.config['cache.enabled']:
      return default

    with self.lock:
      chain = self.__chain_init(user)

      return chain.get(key, default = default)

  def set(self, user, key, value):
    if not self.app.config['cache.enabled']:
      return

    with self.lock:
      chain = self.__chain_init(user)

      chain[key] = value

  def test_and_set(self, user, key, callback, *args, **kwargs):
    # pylint: disable-msg=W0101
    if not self.app.config['cache.enabled']:
      return callback(*args, **kwargs)

    with self.lock:
      chain = self.__chain_init(user)

      if key not in chain:
        chain[key] = callback(*args, **kwargs)

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
          if user.name not in ret:
            ret[user.name] = {}

          ret[user.name] = {'Key': key, 'Size': len(value)}

    return ret
