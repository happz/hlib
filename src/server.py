"""
Simple threaded HTTP server implementation. Based on U{async SocketServer<http://docs.python.org/library/socketserver.html#asynchronous-mixins>} example.
"""

__author__              = 'Milos Prchlik'
__copyright__           = 'Copyright 2010 - 2012, Milos Prchlik'
__contact__             = 'happz@happz.cz'
__license__             = 'http://www.php-suit.com/dpl'

import Queue
import socket
import time
import thread
import threading
import SocketServer
import urllib
import UserDict

import hlib
import hlib.engine
import hlib.error
import hlib.event
import hlib.input
import hlib.http

# pylint: disable-msg=F0401
import hruntime

__all__ = []

class RequestHandler(SocketServer.BaseRequestHandler):
  """
  This class is instantiated for every new request accepted.

  @see:				http://docs.python.org/library/socketserver.html#asynchronous-mixins
  """

  def handle(self):
    """
    Our main processing method. Called by server internals.

      - Read in input data from user, and pass it to request object
      - Trigger C{engine.Request*} events
      - Call proper application handler using requested URL
      - Handle raised exceptions, and modify output when needed.
      - Send output to user
    """

    hruntime.app      = self.server.app
    hruntime.request  = hlib.engine.Request(self)
    hruntime.response = hlib.engine.Response()

    req = hruntime.request
    res = hruntime.response

    def __fail(status, exc = None):
      """
      Called from exception cases, just reset response, set status and log error if we get any.

      @type status:		C{int}
      @param status:		HTTP response code to be set in response.
      @type exc:		L{Exception} descendant.
      @param exc:		Exception that caused this function to be called. Or C{None} in case there was no exception that could be logged (standard errors like L{hlib.http.NotFound}, L{hlib.http.UnknownMethod}, etc.)
      """
      if exc:
        import traceback
        import sys

        traceback.print_exc(file = sys.stderr)

        e = hlib.error.error_from_exception(exc)
        hlib.log.log_error(e)

      res.status = status
      res.output = None

    # Always check there is break at the end...
    while True:
      hlib.event.trigger('engine.RequestConnected', None)

      # In case of exception from read_data sending out response is propably gonna fail. IO error
      # is most likely to be cause of such exception. But we should try anyway.
      try:
        req.read_data(self.request)

      # pylint: disable-msg=W0703
      except Exception, e:
        __fail(500, exc = e)
        break

      # Call parse_data and try to catch all exceptions that may be caused
      # by malformed HTTP input or bad syntax. And lets say it's user's
      # fault, give him HTTP reply code 400.
      try:
        req.parse_data()

      # pylint: disable-msg=W0703
      except hlib.http.NotFound:
        __fail(404)
        break

      except Exception, e:
        __fail(400, exc = e)
        break

      hlib.event.trigger('engine.RequestAccepted', None)

      try:
        req.handler = hruntime.app.get_handler(req.requested)

      except hlib.http.NotFound, e:
        __fail(404)
        break

      io_regime = hlib.handlers.tag_fn_check(req.handler, 'ioregime', None)

      try:
        hlib.event.trigger('engine.RequestStarted', None)

        if not io_regime:
          raise hlib.http.UnknownMethod()

        res.output = io_regime.run_handler()

      except hlib.http.Prohibited:
        __fail(403)

      except hlib.http.NotFound:
        __fail(404)

      except hlib.http.UnknownMethod:
        __fail(405)

      except hlib.http.Redirect, e:
        if req.base:
          url = 'http://' + req.base
        else:
          url = ''

        url += e.location

        io_regime.redirect(url)

      except hlib.error.BaseError, e:
        hlib.log.log_error(e)

        res.status = 500

      except Exception, e:
        __fail(500, exc = e)

      # This one is pretty important ;)
      break

    output = res.dumps()

    hlib.event.trigger('engine.RequestFinished', None)

    try:
      self.request.sendall(output)

    # pylint: disable-msg=W0703
    except Exception, e:
      # Just log error, nothing else to do - it's too late
      __fail(0, exc = e)

    else:
      req.written_bytes += len(output)

    hlib.event.trigger('engine.RequestClosed', None)

class ThreadPool(object):
  """
  Represents pool of threads, manages number of running threads and distributes new requests to waiting threads.
  """

  def __init__(self, server, limit = None):
    """
    @type server:		L{hlib.server.Server}
    @param server:		Server this pool belongs to.
    @type limit:		C{int}
    @param limit:		Maximal number of running threads. Default is C{None} which means "no limit".
    """

    super(ThreadPool, self).__init__()

    self.limit		= limit
    self.server		= server

    self.lock		= threading.RLock()
    self.current_count	= 0
    self.free_count	= 0
    self.queue		= Queue.Queue()

    self.threads	= {}

    self.stats_name	= 'Pool (%s)' % self.server.name

    hlib.event.Hook('engine.ThreadStarted', 'hlib.server.ThreadPool(%s)' % self.server.name, self.on_thread_start)
    hlib.event.Hook('engine.ThreadFinished', 'hlib.server.ThreadPool(%s)' % self.server.name, self.on_thread_finished)
    hlib.event.Hook('engine.RequestConnected', 'hlib.server.ThreadPool(%s)' % self.server.name, self.on_request_connected)
    hlib.event.Hook('engine.RequestFinished',  'hlib.server.ThreadPool(%s)' % self.server.name, self.on_request_finished)

  # Event handlers
  def on_thread_start(self, _):
    hruntime.tid = threading.current_thread().name

    d = {
      'Start time':			time.time(),
      'Uptime':				lambda s: time.time() - s['Start time'],

      'Total bytes read':		0,
      'Total bytes written':		0,
      'Total requests':			0,
      'Total time':			0
    }

    from hlib.stats import stats, stats_lock

    with stats_lock:
      stats[self.stats_name]['Threads'][hruntime.tid] = d

      stats[self.stats_name]['Total threads started'] += 1

  def on_thread_finished(self, _):
    from hlib.stats import stats, stats_lock

    with stats_lock:
      del stats[self.stats_name]['Threads'][hruntime.tid]

      stats[self.stats_name]['Total threads finished'] += 1

  def on_request_connected(self, _):
    from hlib.stats import stats, stats_lock

    with stats_lock:
      stats[self.stats_name]['Threads'][hruntime.tid]['Total requests'] += 1

  def on_request_finished(self, _):
    from hlib.stats import stats, stats_lock

    with stats_lock:
      ri = hruntime.request
      t = time.time() - ri.ctime

      d = stats[self.stats_name]['Threads'][hruntime.tid]
      d['Total bytes read']		+= ri.read_bytes
      d['Total bytes written']		+= ri.written_bytes
      d['Total time']			+= t

      d = stats[self.server.engine.stats_name]
      d['Total bytes read']		+= ri.read_bytes
      d['Total bytes written']		+= ri.written_bytes
      d['Total time']			+= t

  def get_request(self):
    """
    Block until there is new, unassigned request we can grab. Called by threads to acquire new requests.

    @rtype:			C{tuple}
    @return:			request info as pushed to queue by L{add_request}.
    """

    req = self.queue.get()
    with self.lock:
      self.free_count -= 1

    return req

  def finish_request(self):
    """
    Called by threads when request is finished.
    """

    with self.lock:
      self.free_count += 1

    self.queue.task_done()

  def add_request(self, request, client_address):
    """
    Add new request to queue. Start new thread if there are no free threads and number of running threads is lesser than C{limit}.
    
    Request is pushed to queue as C{tuple} (C{request}, C{client_address}).

    @see:			L{Server.process_request}
    @type request:              L{socket._socketobject}
    @param request:             Current request' socket
    @type client_address:       C{tuple}
    @param client_address:      Tuple (C{string}, C{int}) of C{client' IP address}, C{client' IP port}
    """

    with self.lock:
      if self.free_count == 0 and self.current_count < self.limit:
        self.add_thread()

    self.queue.put((request, client_address))

  def add_thread(self):
    with self.lock:
      t = threading.Thread(target = self.server.process_request_thread, name = 'worker-' + str(self.current_count + 1), args = (self,))
      t.setDaemon(1)
      t.start()

      self.threads[t.name] = t

      self.current_count += 1
      self.free_count += 1

  def remove_thread(self):
    with self.lock:
      del self.threads[hruntime.tid]

  def init_stats(self):
    # pylint: disable-msg=W0621
    import hlib.stats

    hlib.stats.init_namespace('Pool (%s)' % self.server.name, {
      'Queue size':		lambda s: self.queue.qsize(),
      'Current threads':	lambda s: self.current_count,
      'Free threads':		lambda s: self.free_count,

      'Total threads started':	0,
      'Total threads finished':	0,

      'Threads':		{}
    })

  def start(self):
    self.init_stats()

  def stop(self):
    with self.lock:
      for _ in range(0, self.current_count):
        self.queue.put(None)

    sleep = True
    while sleep:
      with self.lock:
        if len(self.threads) <= 0:
          sleep = False
          time.sleep(0)

class Server(SocketServer.TCPServer):
  """
  This class represents one HTTP server.
  """

  def __init__(self, engine, name, config, *args, **kwargs):
    """
    Instantiate Server object. Setup server properties, prepare sockets, etc... Pass C{args} and C{kwargs} to parenting class, these include server' bind address and port, and request handler class.

    Server does NOT start yet - L{start} method has to be called to really start server.

    @see:			http://docs.python.org/library/socketserver.html#asynchronous-mixins
    """

    self.engine			= engine
    self.name			= name
    self.config			= config
    self.server_thread		= None
    self.allow_reuse_address	= True

    SocketServer.TCPServer.__init__(self, *args, **kwargs)

    self.pool			= ThreadPool(self, limit = self.config.get('pool.max', 10))
    self.app			= config['app']

    self.shutting_down		= False

  @staticmethod
  def default_config():
    c = {}

    c['host']			= 'localhost'
    c['port']			= 8080
    c['compress']		= True
    c['pool.max']		= 10

    c['app']			= None

    return c

  def process_request_thread(self, pool):
    """
    This method is running neverending loop, servig requests as they are received by C{pool.get_request()}.

    Raises proper thread-specific events when started and finished (but this method NEVER exists, thus no C{engine.ThreadFinished} event will be ever raised.

    @see:			http://docs.python.org/library/socketserver.html#asynchronous-mixins
    @type pool:			L{ThreadPool}
    @param pool:		Thread pool this thread belongs to. Used for request downstreaming.
    """

    hlib.event.trigger('engine.ThreadStarted', None, server = self)

    while True:
      args = pool.get_request()

      if args == None:
        break

      request, client_address = args

      try:
        self.finish_request(request, client_address)
        self.shutdown_request(request)

      # pylint: disable-msg=W0703
      except Exception, e:
        import sys, traceback
        saved_info = sys.exc_info()
        print >> sys.stderr, '----- ----- ----- Raw exception info ----- ----- -----'
        print >> sys.stderr, 'Exc info:', saved_info
        print >> sys.stderr, ''.join(traceback.format_exception(*saved_info))
        print >> sys.stderr, '----- ----- ----- Raw exception info ----- ----- -----'
        e = hlib.error.error_from_exception(e)
        hlib.log.log_error(e)

        self.handle_error(request, client_address)
        self.shutdown_request(request)

      finally:
        pool.finish_request()

    hlib.event.trigger('engine.ThreadFinished', None, server = self)
    pool.remove_thread()

  def process_request(self, request, client_address):
    """
    Called by L{SocketServer} internals for every new request. Its only job is to call server' thread pool's C{add_request} and pass its arguments.

    @type request:		L{socket._socketobject}
    @param request:		Current request' socket.
    @type client_address:	C{tuple}
    @param client_address:	Tuple (C{string}, C{int}) of client' IP address, client' IP port.
    """

    if self.shutting_down:
      return

    self.pool.add_request(request, client_address)

  def start(self):
    """
    Begin listening on IP port and start accepting requests. Do it in separate (daemon) thread so we can return command to our caller.
    """

    self.pool.start()

    self.server_thread = threading.Thread(target = self.serve_forever, kwargs  = {'poll_interval': 5})
    self.server_thread.daemon = True
    self.server_thread.start()

  def stop(self):
    self.shutting_down = True

    self.shutdown()
    self.pool.stop()
    self.socket.close()
