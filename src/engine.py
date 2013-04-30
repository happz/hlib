"""
Application engine. Classes for defining applications, default engine' event handlers, request/response classes.

@todo:				Add sanity checks for all HTTP input.
"""

__author__              = 'Milos Prchlik'
__copyright__           = 'Copyright 2010 - 2012, Milos Prchlik'
__contact__             = 'happz@happz.cz'
__license__             = 'http://www.php-suit.com/dpl'

import hashlib
import http_parser.util
import ipaddr
import os.path
import pprint
import signal
import StringIO
import sys
import threading
import time
import urllib
import UserDict

try:
  import http_parser.parser as HTTPParser
except ImportError:
  import http_parser.pyparser as HTTPParser

import hlib
import hlib.auth
import hlib.compress
import hlib.error
import hlib.event
import hlib.http
import hlib.http.cookies
import hlib.i18n
import hlib.log
import hlib.server

# pylint: disable-msg=F0401
import hruntime

ENGINES = []
ENGINES_LOCK = threading.RLock()

class AppChannels(object):
  def __init__(self):
    super(AppChannels, self).__init__()

    self.access = []
    self.error = []

class Application(object):
  """
  This class represents one of our applications. Binds together database access, logging channels and tree of handlers.
  """

  def __init__(self, name, root, db, config):
    """
    @type name:			C{string}
    @param name:		Name of application. Any string at all.
    @type root:			L{hlib.handlers.GenericHandler}
    @param root:		Root of tree of handlers.
    @type db:			L{hlib.database.DB}
    @param db:			Database access.
    """

    super(Application, self).__init__()

    self.engines		= []

    self.name                   = name
    self.root                   = root
    self.db			= db
    self.config			= config

    import hlib.cache
    self.cache			= hlib.cache.Cache('Global', self)

    self.channels		= AppChannels()

    self.sessions		= None

    import hlib.api
    self.api_tokens		= hlib.api.ApiTokenCache(self.name, self)

  def __repr__(self):
    return '<hlib.engine.Application(\'%s\', %s, %s, <config>)>' % (self.name, self.root, self.db)

  @staticmethod
  def default_config(app_path):
    c = {}

    c['dir']			= app_path
    c['title']			= None
    c['label']			= None
    c['cache.enabled']		= None

    c['templates.dirs']		= [os.path.join(app_path, 'src', 'templates'), os.path.join(hlib.PATH, 'templates')]
    c['templates.tmp_dir']	= os.path.join(app_path, 'compiled')

    c['pages']			= os.path.join(app_path, 'pages')

    c['mail.server']		= 'localhost'

    c['log.access.format']	= '{date} {time} {request_line} {response_status} {response_length} {request_ip} {request_user}'

    c['sessions.time']		= 2 * 86400
    c['sessions.cookie_name']	= 'hlib_sid'

    return c

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

  All header names are converted to first-letter-capitalized format on all operations (get/set/delete). Used by L{hlib.engine.Request} and L{hlib.engine.Response}.

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

class MultipartPiece(object):
  def __init__(self):
    super(MultipartPiece, self).__init__()

    self.headers = HeaderMap()
    self.data = None

class Request(object):
  def __init__(self, server_handler):
    super(Request, self).__init__()

    self.server_handler	= server_handler
    self.server		= self.server_handler.server

    self.input          = []
    self.parts = []
    self.parser         = HTTPParser.HttpParser()

    self.base		= None
    self.cookies        = {}
    self.handler        = None
    self.headers        = HeaderMap()
    self.http_version   = None
    self.method         = None
    self.params         = {}
    self.params_valid	= False
    self.requested      = None
    self.requested_line	= None

    self.api_token	= None

    self.ctime		= time.time()
    self.read_bytes	= 0
    self.written_bytes	= 0

    self._ips		= None

  requires_login	= property(lambda self: hlib.handlers.tag_fn_check(self.handler, 'require_login', False))
  requires_admin	= property(lambda self: hlib.handlers.tag_fn_check(self.handler, 'require_admin', False))
  requires_write	= property(lambda self: hlib.handlers.tag_fn_check(self.handler, 'require_write', False))
  requires_hosts	= property(lambda self: hlib.handlers.tag_fn_check(self.handler, 'require_hosts', False))

  is_prohibited		= property(lambda self: hlib.handlers.tag_fn_check(self.handler, 'prohibited', False))
  is_tainted		= property(lambda self: hruntime.session != None and hasattr(hruntime.session, 'tainted') and hruntime.session.tainted != False)
  is_authenticated = property(lambda self: hruntime.session != None and hasattr(hruntime.session, 'authenticated') and hruntime.session.authenticated == True)

  @property
  def ips(self):
    try:
      if 'X-Forwarded-For' not in self.headers:
        return [ipaddr.IPAddress(self.server_handler.client_address[0])]

      entries = [e.strip() for e in self.headers['X-Forwarded-For'].split(',')]
      filtered_entries = []

      while len(entries) > 0:
        entry = entries.pop(0)
        if len(entry.split('.')) < 4:
          entry = entry + entries.pop(0)
        filtered_entries.append(entry)

      entries = [e.strip() for e in self.headers['X-Forwarded-For'].split(',')]

      if len(entries) != len(filtered_entries):
        print >> sys.stderr, 'Bad X-Forwarded-For: "%s" vs "%s"' % (str(entries), str(filtered_entries))

      return [ipaddr.IPAddress(self.server_handler.client_address[0])] + ([ipaddr.IPAddress(ip.strip()) for ip in filtered_entries])

    except ValueError, e:
      print >> sys.stderr, '----- ----- Invalid IP address ----- -----'
      print >> sys.stderr, e
      print >> sys.stderr, 'Client address:', self.server_handler.client_address
      print >> sys.stderr, 'X-Forwarded-For:', self.headers['X-Forwarded-For']
      return []

  def read_data(self, socket):
    while True:
      data = socket.recv(1024)

      if not data:
        break

      len_recv = len(data)
      len_parsed = self.parser.execute(data, len_recv)

      if len_recv != len_parsed:
        raise hlib.http.BadRequest()

      if self.parser.is_partial_body():
        self.input.append(self.parser.recv_body())

      self.read_bytes += len_recv

      if self.parser.is_message_complete():
        break

  def parse_data(self):
    if not self.parser.is_headers_complete():
      raise hlib.http.BadRequest()

    if not self.parser.is_message_complete():
      raise hlib.http.BadRequest()

    self.input = http_parser.util.b('').join(self.input).strip()

    self.requested_line = '%s %s' % (self.parser.get_method(), self.parser.get_path())
    self.requested = self.parser.get_path()

    for key, value in self.parser.get_headers().items():
      self.headers[key] = value

    post_data = self.input.strip()

    if 'Host' in self.headers:
      self.base = self.headers['Host']

    if self.parser.get_method().lower() not in ['get', 'post']:
      raise hlib.http.UnknownMethod(self.parser.get_method())

    def __parse_param(s):
      l = s.strip().split('=')
      if len(l) < 2:
        raise hlib.http.BadRequest()

      n = l[0].strip()
      v = urllib.unquote_plus('='.join(l[1:]).strip())

      return (n, v)

    def __parse_params(ps):
      for param in ps.split('&'):
        n, v = __parse_param(param)

        self.params[n] = v

    # Parse cookies
    if 'Cookie' in self.headers:
      for cookie in self.headers['Cookie'].split(';'):
        n, v = __parse_param(cookie)
        self.cookies[n] = hlib.http.cookies.Cookie(n, value = v, server = self.server, max_age = hruntime.app.config['sessions.time'])

    for cookie in self.cookies.values():
      if cookie.name.startswith('SpryMedia_DataTables'):
        cookie.delete()

    # Parse GET params
    if len(self.parser.get_query_string()) > 0:
      __parse_params(self.parser.get_query_string())

    # Parse POST params
    if 'Content-Type' in self.headers:
      ct = self.headers['Content-Type']

      if ct.startswith('application/x-www-form-urlencoded'):
        if len(self.input) <= 0:
          pass
          #raise hlib.http.BadRequest('Content-Type == x-www-form-urlencoded and empty body')
        else:
          __parse_params(self.input)

      elif ct.startswith('multipart/form-data'):
        i = ct.find('boundary=')
        if i < 0:
          raise hlib.http.BadRequest('Content-Type == multipart/form-data and no boundary')
        boundary = '--' + ct[i + len('boundary='):]

        start = self.input.find(boundary, 0)
        if start < 0:
          raise hlib.http.BadRequest('Inconsistent boundary')

        end = self.input.find(boundary, start + 1)
        if end < 0:
          raise hlib.http.BadRequest('Inconsistent boundary')

        stream = StringIO.StringIO(self.input[start:end])
        piece = MultipartPiece()

        while True:
          l = stream.readline().strip()
          if len(l) <= 0:
            break

          if l == boundary:
            continue

          k = l.split(':')
          if len(k) != 2:
            raise hlib.http.BadRequest('Malformed header in multipart piece: "%s"' % l)
          piece.headers[k[0].strip()] = k[1].strip()

        piece.data = stream.read()
        self.parts.append(piece)

    # Restore session if any
    sid_cookie_name = hruntime.app.config['sessions.cookie_name']
    if sid_cookie_name in self.cookies:
      cookie = self.cookies[sid_cookie_name]

      if hruntime.app.sessions.exists(cookie.value):
        session = hruntime.app.sessions.load(cookie.value)

      else:
        session = hlib.http.session.Session.create()

    else:
      session = hlib.http.session.Session.create()

    if session.check():
      hruntime.session = session
    else:
      session.destroy()
      hruntime.session = None

class Response(object):
  def __init__(self):
    super(Response, self).__init__()

    self.cookies		= {}
    self.status                 = 200
    self.headers                = HeaderMap()
    self.location		= None
    self.time			= hruntime.time

    self._output                = None
    self.output_length		= None

    self._raw_output		= None
    self.raw_output_length	= None

    self.output			= None
    self.raw_output		= None

  def __getattr__(self, name):
    if name == 'output':
      return self._output

    if name == 'raw_output':
      return self._raw_output

    raise AttributeError(name)

  def __setattr__(self, name, value):
    if name == 'output':
      self._output = value

      if value == None:
        self.output_length = None
      else:
        self.output_length = len(value)

    if name == 'raw_output':
      self._raw_output = value

      if value == None:
        self.raw_output_length = None
      else:
        self.raw_output_length = len(value)

    super(Response, self).__setattr__(name, value)

  def dumps(self):
    req = hruntime.request

    self.headers['Connection'] = 'close'

    if 'Host' in req.headers:
      self.headers['Host'] = req.headers['Host']

    if hruntime.session != None:
      hruntime.session.save()

      sid_cookie_name = hruntime.app.config['sessions.cookie_name']
      if sid_cookie_name not in req.cookies or req.cookies[sid_cookie_name].value != hruntime.session.sid:
        session_cookie = hlib.http.cookies.Cookie(sid_cookie_name, value = hruntime.session.sid, server = req.server, max_age = hruntime.app.config['sessions.time'])
      else:
        session_cookie = req.cookies[sid_cookie_name]

      self.cookies[sid_cookie_name] = session_cookie

    for name, cookie in self.cookies.iteritems():
      self.headers['Set-Cookie'] = '%s=%s; Max-Age=%s; Path=%s' % (cookie.name, urllib.quote(cookie.value), cookie.max_age, cookie.path)

    if self.output:
      if hasattr(req.server.config, 'compress') and req.server.config.compress == True:
        compressed = hlib.compress.compress(self.output)

        self.raw_output = self.output

        self.output = compressed

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

  def __init__(self, server_configs):
    super(Engine, self).__init__()

    self.servers	= []
    self.apps		= {}

    i = 0
    for sc in server_configs:
      self.apps[sc['app'].name] = sc['app']
      sc['app'].engines.append(self)

      server = hlib.server.Server(self, 'server-%i' % i, sc, (sc['host'], sc['port']), hlib.server.RequestHandler)
      self.servers.append(server)

      i += 1

    self.stats_name		= 'Engine'

    # Set up event handlers
    signal.signal(signal.SIGHUP, self.on_sighup)
    signal.signal(signal.SIGUSR1, self.on_sigusr1)
    hlib.event.Hook('engine.ThreadStarted',    'hlib.engine.Engine', self.on_thread_start)
    hlib.event.Hook('engine.ThreadFinished'  , 'hlib.engine.Engine', self.on_thread_finished)
    hlib.event.Hook('engine.RequestConnected', 'hlib.engine.Engine', self.on_request_connected)
    hlib.event.Hook('engine.RequestAccepted',  'hlib.engine.Engine', self.on_request_accepted)
    hlib.event.Hook('engine.RequestStarted',   'hlib.engine.Engine', self.on_request_started)
    hlib.event.Hook('engine.RequestFinished',  'hlib.engine.Engine', self.on_request_finished)
    hlib.event.Hook('engine.RequestClosed',    'hlib.engine.Engine', self.on_request_closed)
    hlib.event.Hook('engine.Halted',           'hlib.engine.Engine', self.on_engine_halted)

    with ENGINES_LOCK:
      ENGINES.append(self)

  def on_sighup(self, signum, frame):
    if signum != signal.SIGHUP:
      return

    hlib.config['log.channels.error'].reopen()

    for app in self.apps.values():
      print 'Reopening channels for app %s' % app.name

      for c in app.channels.access:
        c.reopen()
      for c in app.channels.error:
        c.reopen()

  def on_sigusr1(self, signum, frame):
    if signum != signal.SIGUSR1:
      return

    with ENGINES_LOCK:
      for engine in ENGINES:
        for server in engine.servers:
          server.stop()

      for engine in ENGINES:
        for app in engine.apps.values():
          for c in app.channels.access:
            c.close()

          for c in app.channels.error:
            c.close()

          if not app.db:
            continue

          app.db.close()
          app.db = None

    print 'Restarting application'

    os.execv(sys.argv[0], sys.argv[:])

  def on_thread_start(self, e):
    """
    Default hlib handler for C{engine.ThreadStarted} event.

    Set up thread enviroment (L{hruntime} variables) and open database connection.

    @type e:			L{hlib.events.engine.ThreadStarted}
    @param e:			Current event.
    """

    hruntime.reset_locals()

    hruntime.tid		= threading.current_thread().name
    hruntime.db			= e.server.app.db
    hruntime.root		= e.server.app.root

    dbconn, dbroot = hruntime.db.connect()
    hruntime.db.start_transaction()

    hruntime.dbconn = dbconn
    hruntime.dbroot = dbroot

    if 'root' in dbroot:
      hruntime.dbroot = dbroot['root']
      hruntime.db.rollback()

    hruntime.__init_done	= True

  def on_thread_finished(self, _):
    """
    Default hlib handler for C{engine.ThreadFinished} event.
    """

    hruntime.dbconn.close()

  def on_request_connected(self, _):
    from hlib.stats import stats, stats_lock

    d = {
      'Bytes read':                     0,
      'Bytes written':                  0,
      'Client':                         hlib.ips_to_str(hruntime.request.ips),
      'Start time':                     hruntime.time,
      'Requested line':                 None
    }

    with stats_lock:
      stats[self.stats_name]['Total requests'] += 1
      stats[self.stats_name]['Requests'][hruntime.tid] = d

  def on_request_accepted(self, _):
    from hlib.stats import stats, stats_lock

    with stats_lock:
      d = stats[self.stats_name]['Requests'][hruntime.tid]

      d['Client']                         = hlib.ips_to_str(hruntime.request.ips)
      d['Requested line']                 = hruntime.request.requested_line

  def on_request_started(self, _):
    """
    Default hlib handler for C{engine.RequestStarted} event.

    Prepare enviroment for (and based on) new request. Reset L{hruntime} properties to default values, start new db transaction, and check basic access controls for new request.

    @raise hlib.http.Prohibited:	Raised when requested resource is marked as prohibited (using L{hlib.handlers.prohibited})
    @raise hlib.http.Redirect:	Raised when requested resource is admin-access only (using L{hlib.handlers.require_admin}). Also can be raised by internal call to L{hlib.auth.check_session}.
    """

    hruntime.db.start_transaction()
    hruntime.clean()

    req = hruntime.request

    if req.requires_hosts:
      hosts_allowed = req.requires_hosts()
      hosts_present = req.ips

      def __check_host(h):
        for host_allowed in hosts_allowed:
          if type(host_allowed) in (ipaddr.IPv4Address, ipaddr.IPv6Address) and h == host_allowed:
            return True
          if type(host_allowed) in (ipaddr.IPv4Network, ipaddr.IPv6Network) and h in host_allowed:
            return True

        return False

      if len(hosts_present) <= 0:
        # handler has require_hosts but client present no address => fail
        passed = False

      elif len(hosts_present) == 1:
        passed = __check_host(hosts_present[0])

      elif len(hosts_present) > 1:
        passed = __check_host(hosts_present[1])

      if passed != True:
        raise hlib.http.Prohibited()

    if req.requires_login:
      io_regime = hlib.handlers.tag_fn_check(req.handler, 'ioregime', None)
      if not io_regime:
        raise hlib.http.Prohibited()

      io_regime.check_session()

    if req.is_prohibited:
      hruntime.dont_commit = True

      raise hlib.http.Prohibited()

    if hruntime.dbroot.server.maintenance_mode == True and req.requires_login and hruntime.user.maintenance_access != True:
      hruntime.dont_commit = True
      raise hlib.http.Redirect('/maintenance/')

    if req.requires_admin:
      if not hruntime.user.is_admin:
        hruntime.dont_commit = True
        raise hlib.http.Redirect('/admin/')

  def on_request_finished(self, _):
    """
    Default hlib handler for C{engine.RequestFinished} event.

    Clean up after finished request. Log access into access log, commit (or rollback) database changes.
    """

    hlib.log.log_access()

    from hlib.stats import stats, stats_lock

    def __update_stats(engine_stat):
      # pylint: disable-msg=W0613
      with stats_lock:
        stats[self.stats_name][engine_stat] += 1

    if not hruntime.request.handler:
      hruntime.db.rollback()
      __update_stats('Missing handlers')
      return

    if hruntime.request.requires_write != True:
      hruntime.db.rollback()
      __update_stats('RO requests')
      return

    if hruntime.dont_commit != False:
      hruntime.db.rollback()
      __update_stats('Forced RO requests')
      return

    if hruntime.db.commit() == True:
      return

    __update_stats('Failed commits')
    hruntime.db.rollback()

  def on_request_closed(self, _):
    """
    Default hlib handler for C{engine.RequestFinished} event.

    Clean up after finished request, and update statistics.
    """

    from hlib.stats import stats, stats_lock

    with stats_lock:
      del stats[self.stats_name]['Requests'][hruntime.tid]

  def on_engine_halted(self, _):
    """
    Default hlib handler for C{engine.Halted} event.

    For now, just dump statistics and language coverage data.
    """

    # pylint: disable-msg=W0621
    import hlib.stats
    stats_copy = hlib.stats.snapshot(hlib.stats.stats)

    pprint.pprint(stats_copy)

    for app in self.apps.values():
      if app.cache:
        print
        print app.cache.stats_name

        for user, chain in app.cache.objects.items():
          print '  %s' % user.name.encode('ascii', 'replace')
          for key, value in chain.items():
            print '    "%s" = %s, size %i' % (key, type(value), len(value))

  def init_stats(self):
    import hlib.stats
    hlib.stats.init_namespace('Engine', {
      'Current time':             lambda s: hruntime.time,
      'Current requests':         lambda s: len(s['Requests']),

      'Start time':               time.time(),
      'Uptime':                   lambda s: time.time() - s['Start time'],

      'Total bytes read':         0,
      'Total bytes written':      0,
      'Total requests':           0,
      'Total time':                       0,

      'Bytes read/second':        lambda s: s['Total bytes read'] / s['Uptime'](s),
      'Bytes written/second':     lambda s: s['Total bytes written'] / s['Uptime'](s),
      'Bytes read/request':       lambda s: (s['Total requests'] and (s['Total bytes read'] / float(s['Total requests'])) or 0.0),
      'Bytes written/request':    lambda s: (s['Total requests'] and (s['Total bytes written'] / float(s['Total requests'])) or 0.0),
      'Requests/second':          lambda s: float(s['Total requests']) / s['Uptime'](s),

      'Requests':                 {},

      'Missing handlers':	0,
      'RO requests':		0,
      'Forced RO requests':	0,
      'Failed commits':		0,
    })

  def start(self):
    self.init_stats()

    hlib.event.trigger('engine.Started', None, post = False)

    for s in self.servers:
      s.start()

    try:
      while True:
        time.sleep(100)
        time.sleep(0)     # yield

    except KeyboardInterrupt:
      for server in self.servers:
        server.stop()

      hlib.event.trigger('engine.Halted', None)

      sys.exit(0)
