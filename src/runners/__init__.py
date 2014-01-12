__author__ = 'Milos Prchlik'
__copyright__ = 'Copyright 2010 - 2013, Milos Prchlik'
__contact__ = 'happz@happz.cz'
__license__ = 'http://www.php-suit.com/dpl'

import ConfigParser
import ipaddr
import os.path
import signal
import sys

import hlib.database
import hlib.engine
import hlib.events
import hlib.http.session
import hlib.log.channels.file
import hlib.log.channels.stderr
import hlib.server

import hruntime  # @UnresolvedImport

hruntime.tid = 'Master thread'

class ConfigFile(ConfigParser.ConfigParser):
  def __init__(self, default = None):
    ConfigParser.ConfigParser.__init__(self)

    self.default = default or {}

  def get(self, section, option):
    if self.has_option(section, option):
      return ConfigParser.ConfigParser.get(self, section, option)

    if section not in self.default:
      raise ConfigParser.NoSectionError(section)

    if option not in self.default[section]:
      raise ConfigParser.NoOptionError(section, option)

    return self.default[section][option]

class Runner(object):
  def on_sighup(self, signum, frame):
    if signum != signal.SIGHUP:
      return

    hlib.events.trigger('system.LogReload', None)

  def on_sigusr1(self, signum, frame):
    if signum != signal.SIGUSR1:
      return

    hlib.events.trigger('system.SystemReload', None)

    print 'Restarting application'

    os.execv(sys.argv[0], sys.argv[:])

  def __init__(self, config_file, root, config_defaults = None, on_app_config = None):
    super(Runner, self).__init__()

    config = ConfigFile(default = config_defaults)
    config.read(config_file)

    # Setup channels - error, access and transactions
    stderr = hlib.log.channels.stderr.Channel()

    def __get_channel(name):
      if config.get('log', name):
        p = config.get('log', name)
      else:
        p = os.path.join(config.get('server', 'path'), 'logs', name + '.log')

      return hlib.log.channels.file.Channel(p)

    access = __get_channel('access')
    error = __get_channel('error')
    transactions = __get_channel('transactions')
    events = __get_channel('events')

    # Setup database
    db_address = hlib.database.DBAddress(config.get('database', 'address'))
    db = hlib.database.DB('main db', db_address, cache_size = int(config.get('database', 'cache_size')), pool_size = int(config.get('server', 'queue.workers')) + 1)
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
    # app.sessions = hlib.http.session.FileStorage(config.get('session', 'storage_path'), app)
    app.sessions = hlib.http.session.FileBackedMemoryStorage(config.get('session', 'storage_path'), app)
    app.config['sessions.time']   = config.get('session', 'time')
    app.config['sessions.cookie_name']  = config.get('session', 'cookie_name')

    app.config['log.access.format'] = config.get('log', 'access_format')
    app.channels.add('access', access)
    app.channels.add('error', stderr, error)
    app.channels.add('transactions', transactions)
    app.channels.add('events', stderr, events)

    if on_app_config:
      on_app_config(app, config)

    server_config = hlib.server.Server.default_config()
    server_config['server'] = config.get('server', 'host')
    server_config['port']   = int(config.get('server', 'port'))
    server_config['app']    = app
    server_config['queue.workers'] = int(config.get('server', 'queue.workers'))
    server_config['queue.timeout'] = int(config.get('server', 'queue.timeout'))
    server_config['queue.size'] = int(config.get('server', 'queue.size'))

    self.engine = hlib.engine.Engine('Engine #1', [server_config])

    signal.signal(signal.SIGHUP, self.on_sighup)
    signal.signal(signal.SIGUSR1, self.on_sigusr1)

  def run(self):
    self.engine.start()
