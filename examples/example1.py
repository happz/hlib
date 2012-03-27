import hlib
import hlib.engine
import hlib.handlers
import hlib.log.channels.stderr, hlib.log.channels.file

class RootHandler(hlib.handlers.GenericHandler):
  @hlib.handlers.page
  def index(self):
    return '<html>Hello, world!</html>'

stderr = hlib.log.channels.stderr.Channel()
access = hlib.log.channels.file.Channel('/tmp/hlib-example-access.log')
error  = hlib.log.channels.file.Channel('/tmp/hlib-example-error.log')

hlib.config.log.channels.error = stderr

db_address = hlib.database.DBAddress('FileStorage:::::/tmp/hlib-example.db')
db = hlib.database.DB(db_address)
db.open()

server = hlib.Config()
server.host = 'localhost'
server.port = 8080
server.max_threads = 2
server.compress = False

server.app = hlib.engine.Application('settlers', RootHandler(), db, title = 'Hlib - Example1')
server.app.channels.access = [stderr, access]
server.app.channels.error  = [stderr, error]

engine = hlib.engine.Engine([server])
engine.start()
