import pprint
import threading

class Cache(object):
  def __init__(self, name, app):
    super(Cache, self).__init__()

    self.name		= name
    self.app		= app

    self.lock		= threading.RLock()
    self.objects	= {}

    import hlib.stats	# Don't import as global, => circular imports :'(
    with hlib.stats.stats_lock:
      hlib.stats.stats['Cache (%s)' % self.name] = {
        'Total objects':	lambda s: sum([len(chain) for chain in self.objects.values()]),
        'Total chains':		lambda s: len(self.objects),
        'Total size':		lambda s: sum([sum([len(v) for v in chain.values()]) for chain in self.objects.values()]),
        'Hits':			0,
        'Misses':		0,
        'Inserts':		0,
        'Chains':		lambda s: self.to_stats()
      }

  def __chain_init(self, user):
    if user.name not in self.objects:
      self.objects[user.name] = {}

    return self.objects[user.name]

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
      self.__chain_init(user)

      if key not in self.objects[user.name]:
        self.objects[user.name][key] = callback(*args, **kwargs)

      return self.objects[user.name][key]

  def remove(self, user, key):
    with self.lock:
      self.__chain_init(user)

      if key in self.objects[user.name]:
        del self.objects[user.name][key]

  def to_stats(self):
    ret = []

    with self.lock:
      for username, chain in self.objects.iteritems():
        for key, value in chain.iteritems():
          ret.append({
            'User':		username,
            'Key':		key,
            'Size':		len(value)
          })

    return ret
