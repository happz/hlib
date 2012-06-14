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

hlib.config['log.channels.error'] = stderr

db_address = hlib.database.DBAddress('FileStorage:::::/tmp/hlib-example.db')
db = hlib.database.DB(db_address)
db.open()

app_config			= hlib.engine.Application.default_config('/path/to/source/code')
app_config['title']		= 'Testing app'

app = hlib.engine.Application('app', RootHandler(), db, app_config)

app.sessions = hlib.http.session.FileStorage('/tmp/sessions.dat', app)
app.config['sessions.time']	= 2 * 86400
app.config['sessions.cookie_name'] = 'app_sid'

app.config['log.access.format']	= '{date} {time} - {request_line} - {response_status} {response_length} - {request_ip} {request_user}'
app.channels.access = [stderr, access]
app.channels.error  = [stderr, error]

server_config			= hlib.server.Server.default_config()
server_config['server']		= 'localhost'
server_config['port']		= 8080
server_config['app']		= app

engine = hlib.engine.Engine([server_config])
engine.start()
