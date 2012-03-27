"""
Functions for access library enviroment from external programs. Sets the enviroment up as if code
is present in main library code.

@author:                        Milos Prchlik
@contact:                       U{happz@happz.cz}
@license:                       DPL (U{http://www.php-suit.com/dpl})
"""

import ConfigParser

import hlib
import hlib.database
import hlib.datalayer
import hlib.engine
import hlib.handlers.root
import hlib.log.channels.stderr
import hlib.server

def init_env(config_file):
  """
  Read specified configuration file and create and init database access.

  @type config_file:            string
  @param config_file:           Path to configuration file to be read
  """

  config = ConfigParser.ConfigParser()
  config.read(config_file)

  stderr = hlib.log.channels.stderr.Channel()

  # pylint: disable-msg=E1101
  hlib.config.log.channels.error = stderr

  db_address = hlib.database.DBAddress(config.get('database', 'address'))
  db = hlib.database.DB(db_address)
  db.open()

  server = hlib.Config()
  server.host = config.get('server', 'host')
  server.port = int(config.get('server', 'port'))
  server.max_threads = 1

  server.app = hlib.engine.Application('settlers', hlib.handlers.root.Handler(), db, title = 'Hlib env')
  server.app.channels.access = [stderr]
  server.app.channels.error  = [stderr]

  server = hlib.server.Server(server, (server.host, server.port), hlib.server.RequestHandler)

  hlib.event.trigger('engine.ThreadStarted', None, server = server)
