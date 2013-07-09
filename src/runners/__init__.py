import ipaddr
import os.path

import hlib
import hlib.engine
import hlib.event
import hlib.log.channels.file
import hlib.log.channels.stderr

import hruntime

hruntime.tid = None

class Runner(object):
  def __init__(self, config_file, root, config_defaults = None, on_app_config = None):
    super(Runner, self).__init__()

    config = hlib.ConfigFile(default = config_defaults)
    config.read(config_file)

    # Setup channels - error, access and transactions
    stderr = hlib.log.channels.stderr.Channel()

    def __get_channel(name):
      if config.get('log', name):
        p = config.get('log', name)
        c = hlib.log.channels.file.Channel(config.get('log', name))
      else:
        p = os.path.join(config.get('server', 'path'), 'logs', name + '.log')

      return hlib.log.channels.file.Channel(p)

    access = __get_channel('access')
    error = __get_channel('error')
    transactions = __get_channel('transactions')

    hlib.config['log.channels.error'] = stderr

    # Setup database
    db_address = hlib.database.DBAddress(config.get('database', 'address'))
    db = hlib.database.DB('main db', db_address, cache_size = 35000, pool_size = int(config.get('server', 'pool.max')) + 2)
    db.open()

    # Create application
    app_config = hlib.engine.Application.default_config(config.get('server', 'path'))
    app_config['title'] = config.get('web', 'title')
    app_config['label'] = config.get('web', 'label')

    app_config['cache.enabled'] = bool(config.get('cache', 'enabled'))
    for token in config.get('cache', 'dont_cache').split(','):
      app_config['cache.dont_cache.' + token.strip()] = True

    app_config['hosts']   = {}
    if config.has_section('hosts'):
      for option in config.options('hosts'):
        addresses = config.get('hosts', option)
        app_config['hosts'][option] = [(ipaddr.IPNetwork(addr.strip()) if '/' in addr else ipaddr.IPAddress(addr.strip())) for addr in addresses.strip().split(',')]

    app_config['stats'] = {}
    if config.has_section('stats'):
      for option in config.options('stats'):
        app_config['stats.' + option] = config.get('stats', option)

    app_config['issues'] = {
      'token':      config.get('issues', 'token'),
      'repository':   config.get('issues', 'repository')
    }

    app = hlib.engine.Application('settlers', root, db, app_config)
    app.sessions = hlib.http.session.FileStorage(config.get('session', 'storage_path'), app)
    app.config['sessions.time']   = config.get('session', 'time')
    app.config['sessions.cookie_name']  = config.get('session', 'cookie_name')

    app.config['log.access.format'] = config.get('log', 'access_format')
    app.channels.add('access', access)
    app.channels.add('error', stderr, error)
    app.channels.add('transactions', transactions)

    if on_app_config:
      on_app_config(app, config)

    server_config = hlib.server.Server.default_config()
    server_config['server'] = config.get('server', 'host')
    server_config['port']   = int(config.get('server', 'port'))
    server_config['app']    = app
    server_config['pool.max'] = int(config.get('server', 'pool.max'))

    self.engine = hlib.engine.Engine([server_config])

  def run(self):
    print 'Starting...'
    print 'PID = %i' % os.getpid()
    self.engine.start()
