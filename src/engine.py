"""
Application engine. Classes for defining applications, default engine' event handlers, request/response classes.

@todo:				Add sanity checks for all HTTP input.
"""

__author__              = 'Milos Prchlik'
__copyright__           = 'Copyright 2010 - 2012, Milos Prchlik'
__contact__             = 'happz@happz.cz'
__license__             = 'http://www.php-suit.com/dpl'

import hashlib
import pprint
import sys
import thread
import time
import urllib
import UserDict

import hlib
import hlib.auth
import hlib.cache
import hlib.compress
import hlib.error
import hlib.event
import hlib.http
import hlib.http.cookies
import hlib.http.session
import hlib.i18n

import hlib.server

# pylint: disable-msg=F0401
import hruntime

class Application(object):
  """
  This class represents one of our applications. Binds together database access, logging channels and tree of handlers.
  """

  def __init__(self, name, root, db, **kwargs):
    """
    Other additional arguments can be passed as keyword arguments, all will be set as this object properties.

    @type name:			C{string}
    @param name:		Name of application. Any string at all.
    @type root:			L{hlib.handlers.GenericHandler}
    @param root:		Root of tree of handlers.
    @type db:			L{hlib.database.DB}
    @param db:			Database access.
    """

    super(Application, self).__init__()

    self.name                   = name
    self.root                   = root
    self.db			= db
    self.cache			= hlib.cache.Cache(self.name)

    self.channels		= hlib.Config()
    self.channels.access	= []
    self.channels.error		= []

    for k, v in kwargs.iteritems():
      setattr(self, k, v)

  def get_handler(self, requested):
    h = self.root

    for token in requested.split('?')[0].split('/')[1:]:
      if len(token) == 0:
        break

      if hasattr(h, token):
        h = getattr(h, token)
        continue

      raise hlib.http.NotFound()

    if isinstance(h, hlib.handlers.GenericHandler):
      if not hasattr(h, 'index'):
        raise hlib.http.NotFound()

      h = h.index

    return h

class HeaderMap(UserDict.UserDict):
  """
  Dictionary-like object storing HTTP headers and their values.

  All header names are converted to first-letter-capitalized format on all operations (get/set/delete). Used by L{hruntime.request} and L{hruntime.response}.

  @todo:			Support more than 1 header simultaneously (for Cookie header, etc.)
  """

  def __contains__(self, name):
    return UserDict.UserDict.__contains__(self, name.title())

  def __getitem__(self, name):
    return UserDict.UserDict.__getitem__(self, name.title())

  def __setitem__(self, name, value):
    UserDict.UserDict.__setitem__(self, name.title(), value)

  def __delitem__(self, name):
    UserDict.UserDict.__delitem__(self, name.title())

class Request(object):
  def __init__(self, server_handler):
    super(Request, self).__init__()

    self.server_handler	= server_handler
    self.server		= self.server_handler.server

    self.input          = ''

    self.base		= None
    self.cookies        = {}
    self.handler        = None
    self.headers        = HeaderMap()
    self.http_version   = None
    self.method         = None
    self.params         = {}
    self.requested      = None
    self.requested_line	= None

    self.read_bytes	= 0
    self.written_bytes	= 0

  requires_login	= property(lambda self: hlib.handlers.tag_fn_check(self.handler, 'require_login', False))
  requires_admin	= property(lambda self: hlib.handlers.tag_fn_check(self.handler, 'require_admin', False))
  requires_write	= property(lambda self: hlib.handlers.tag_fn_check(self.handler, 'require_write', False))

  is_prohibited		= property(lambda self: hlib.handlers.tag_fn_check(self.handler, 'prohibited', False))
  is_tainted		= property(lambda self: hruntime.session != None and hasattr(hruntime.session, 'tainted'))
  is_authenticated	= property(lambda self: hruntime.session != None and hasattr(hruntime.session, 'authenticated') and hruntime.session.authenticated == True)

  ip			= property(lambda self: [self.server_handler.client_address[0]] + ('X-Forwarded-For' in self.headers and [ip.strip() for ip in self.headers['X-Forwarded-For'].split(',')] or []))

  def read_data(self, socket):
    while True:
      t = socket.recv(1024)

      if len(t) <= 0:
        break

      self.input += t

      l = len(t)
      self.read_bytes += l

      if l < 1024:
        break

  def parse_data(self):
    lines = self.input.split('\n')

    # Parse headers
    i = 0
    for i in range(0, len(lines)):
      line = lines[i].strip()

      if len(line) == 0:
        break

      if i == 0:
        self.requested_line = line

        line = [t for t in line.split(' ') if len(t) > 0]

        self.method = line[0].lower()
        if self.method not in ['get', 'post']:
          raise hlib.http.UnknownMethod(self.method)
 
        self.requested = line[1]

        continue

      line = line.split(':')
      self.headers[line[0].title()] = ':'.join(line[1:]).strip()

    post_data = lines[i + 1].strip()

    if 'Host' in self.headers:
      self.base = self.headers['Host']

    def __parse_param(s):
      l = s.strip().split('=')
      n = l.pop(0).strip()
      v = '='.join(l)
      v = urllib.unquote_plus(v.strip())

      return (n, v)

    def __parse_params(ps):
      for param in ps.split('&'):
        n, v = __parse_param(param)

        self.params[n] = v

    # Parse GET params
    i = self.requested.find('?')
    if i != -1:
      __parse_params(self.requested[i + 1:])

    # Parse POST params
    if len(post_data) > 0:
      __parse_params(post_data)

    # Parse cookies
    if 'Cookie' in self.headers:
      for cookie in self.headers['Cookie'].split(';'):
        n, v = __parse_param(cookie)

        self.cookies[n] = hlib.http.cookies.Cookie(n, value = v)

    # Restore session if any
    if 'settlers_sid' in self.cookies:
      cookie = self.cookies['settlers_sid']

      if hlib.http.session.Session.exists(cookie.value):
        session = hlib.http.session.Session.load(cookie.value)

      else:
        session = hlib.http.session.Session.create(self)

    else:
      session = hlib.http.session.Session.create(self)

    if session.check(hruntime.request):
      hruntime.session = session
    else:
      session.destroy()

class Response(object):
  def __init__(self):
    super(Response, self).__init__()

    self.cookies		= {}
    self.status                 = 200
    self.headers                = HeaderMap()
    self.location		= None
    self.output                 = None
    self.output_length		= None
    self.time			= hruntime.time

    self.raw_output		= None
    self.raw_output_length	= None

    self.headers['Content-Type'] = 'text/html; charset=utf-8'

  def dumps(self):
    self.headers['Connection'] = 'close'

    if 'Host' in hruntime.request.headers:
      self.headers['Host'] = hruntime.request.headers['Host']

    if hruntime.session != None:
      hruntime.session.save()

      self.cookies['settlers_id'] = hlib.http.cookies.Cookie('settlers_sid', value = hruntime.session.sid)

    for name, cookie in self.cookies.iteritems():
      self.headers['Set-Cookie'] = '%s=%s; expires=%s; Path=%s' % (cookie.name, urllib.quote(cookie.value), cookie.expires, cookie.path)

    if self.output:
      if hruntime.request.server.config.compress == True:
        compressed = hlib.compress.compress(self.output)

        self.raw_output = self.output
        self.raw_output_length = self.output_length

        self.output = compressed
        self.output_length = len(self.output)

        self.headers['Content-Encoding'] = 'gzip'

      self.headers['Content-Length'] = self.output_length

    lines = [
      'HTTP/1.1 %i %s' % (self.status, hlib.http.HTTP_CODES[self.status])
    ]

    for name, value in self.headers.iteritems():
      lines.append('%s: %s' % (name, value))

    lines.append('')

    if self.output != None:
      lines.append(self.output)

    return '\r\n'.join(lines) + '\r\n'

class Engine(object):
  """
  Engine binds servers together.

  Right now there is no need to have more than 1 engine in application. Maybe some day...
  """

  def __init__(self, servers):
    super(Engine, self).__init__()

    self.servers = []

    for server in servers:
      server = hlib.server.Server(server, (server.host, server.port), hlib.server.RequestHandler)
      self.servers.append(server)

  def start(self):
    hlib.event.trigger('engine.Started', None, post = False)

    for s in self.servers:
      s.start()

    try:
      while True:
        time.sleep(100)
        time.sleep(0)     # yield

    except KeyboardInterrupt:
      hlib.event.trigger('engine.Halted', None)

      sys.exit(0)

# pylint: disable-msg=W0613
def __on_thread_start(e):
  """
  Default hlib handler for C{engine.ThreadStarted} event.

  Set up thread enviroment (L{hruntime} variables) and open database connection.

  @type e:			L{hlib.events.engine.ThreadStarted}
  @param e:			Current event.
  """

  hruntime.reset_locals()

  hruntime.tid			= thread.get_ident()
  hruntime.db			= e.server.app.db

  dbconn, dbroot = hruntime.db.connect()
  hruntime.db.start_transaction()

  hruntime.dbconn = dbconn
  hruntime.dbroot = dbroot

  if 'root' in dbroot:
    hruntime.dbroot = dbroot['root']
    hruntime.db.rollback()

  hruntime.__init_done		= True

hlib.event.Hook('engine.ThreadStarted', 'init_hruntime', __on_thread_start)

# pylint: disable-msg=W0613
def __on_thread_finished(e):
  """
  Default hlib handler for C{engine.ThreadFinished} event.

  Unused right now - threads never exits. Maybe some day...
  """

  pass

hlib.event.Hook('engine.ThreadFinished', 'pass', __on_thread_finished)

def __on_request_accepted(e):
  """
  Default hlib handler for C{engine.RequestAccepted} event.

  Unused right now.
  """

  pass

hlib.event.Hook('engine.RequestAccepted', 'hlib_generic', __on_request_accepted)

# pylint: disable-msg=W0613
def __on_request_started(e):
  """
  Default hlib handler for C{engine.RequestStarted} event.

  Prepare enviroment for (and based on) new request. Reset L{hruntime} properties to default values, start new db transaction, and check basic access controls for new request.

  @type e:			L{hlib.events.engine.RequestStarted}
  @param e:			Current event.

  @raise hlib.http.Prohibited:	Raised when requested resource is marked as prohibited (using L{hlib.handlers.prohibited})
  @raise hlib.http.Redirect:	Raised when requested resource is admin-access only (using L{hlib.handlers.require_admin}). Also can be raised by internal call to L{hlib.auth.check_session}.
  """

  hruntime.db.start_transaction()

  hruntime.user			= None
  hruntime.dont_commit		= False
  hruntime.ui_form		= None
  hruntime.time			= None

  req = hruntime.request

  if req.requires_login:
    hlib.auth.check_session()

  if req.is_prohibited:
    hruntime.dont_commit = True

    raise hlib.http.Prohibited()

  if req.requires_admin:
    if not hruntime.user.is_admin:
      hruntime.dont_commit = True
      raise hlib.http.Redirect('/admin/')

hlib.event.Hook('engine.RequestStarted', 'hlib_generic', __on_request_started)

# pylint: disable-msg=W0613
def __on_request_finished(e):
  """
  Default hlib handler for C{engine.RequestFinished} event.

  Clean up after finished request. Log access into access log and commit (or rollback) database changes.

  @type e:			L{hlib.events.engine.RequestFinished}
  @param e:			Current event.
  """

  hlib.log.log_access()

  if not hruntime.request.handler:
    hruntime.db.rollback()
    return

  if hruntime.request.requires_write != True:
    hruntime.db.rollback()
    return

  if hruntime.dont_commit != False:
    hruntime.db.rollback()
    return

  if hruntime.db.commit() == True:
    return

  hlib.log.log_error(hlib.database.CommitFailedError())

hlib.event.Hook('engine.RequestFinished', 'hlib_generic', __on_request_finished)

# pylint: disable-msg=W0613
def __on_engine_halted(e):
  """
  Default hlib handler for C{engine.Halted} event.

  For now, just dump statistics and language coverage data.
  """

  # pylint: disable-msg=W0621
  import hlib.stats	# Don't import as global, => circular imports :'(
  stats_copy = hlib.stats.snapshot(hlib.stats.stats)
  pprint.pprint(stats_copy)

#  for lang in hruntime.dbroot.localization.languages.itervalues():
#    print lang.hits
#    print lang.misses
#    print lang.get_unused()

hlib.event.Hook('engine.Halted', 'hlib_generic', __on_engine_halted)
