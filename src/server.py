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

hlib.config.servers = []

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
        if not isinstance(e, hlib.error.Error):
          e = hlib.error.ErrorByException(e)

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

      except Exception, e:
        __fail(500, exc = e)
        break

      # Call parse_data and try to catch all exceptions that may be caused
      # by malformed HTTP input or bad syntax. And lets say it's user's
      # fault, give him HTTP reply code 400.
      try:
        req.parse_data()

      except Exception:
        __fail(400, exc = e)
        break

      hlib.event.trigger('engine.RequestAccepted', None)

      try:
        req.handler = hruntime.app.get_handler(req.requested)

      except hlib.http.NotFound, e:
        __fail(404)
        break

      hlib.event.trigger('engine.RequestStarted', None)

      try:
        if hlib.handlers.tag_fn_check(req.handler, 'api', False):
          res.output = hlib.api.run_api_handler()
        else:
          res.output = hlib.handlers.run_page_handler()

        if res.output != None:
          res.output_length = len(res.output)

      except hlib.http.NotFound, e:
        __fail(404)

      except hlib.http.UnknownMethod, e:
        __fail(405)

      except hlib.http.Redirect, e:
        __fail(303)

        if req.base:
          url = 'http://' + req.base
        else:
          url = ''

        url += e.location

        res.headers['Location'] = url

        if 'Content-Type' in res.headers:
          del res.headers['Content-Type']

      except hlib.error.Error, e:
        
        hlib.log.log_error(e)

        res.status = 500

      except Exception, e:
        __fail(500, exc = e)

      # This one is pretty important ;)
      break

    output = res.dumps()

    try:
      self.request.sendall(output)

    except Exception, e:
      # Just log error, nothing else to do - it's too late
      __fail(0, exc = e)

    else:
      req.written_bytes += len(output)

    hlib.event.trigger('engine.RequestFinished', None)

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

    self.lock		= threading.Lock()
    self.current_count	= 0
    self.free_count	= 0
    self.queue		= Queue.Queue()

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
        t = threading.Thread(target = self.server.process_request_thread, args = (self,))
        t.setDaemon(1)
        t.start()

        self.current_count += 1
        self.free_count += 1

    self.queue.put((request, client_address))

class Server(SocketServer.TCPServer):
  """
  This class represents one HTTP server.
  """

  def __init__(self, server, *args, **kwargs):
    """
    Instantiate Server object. Setup server properties, prepare sockets, etc... Pass C{args} and C{kwargs} to parenting class, these include server' bind address and port, and request handler class.

    Server does NOT start yet - L{start} method has to be called to really start server.

    @see:			http://docs.python.org/library/socketserver.html#asynchronous-mixins
    @type server:		L{hlib.Config}
    @param server:		Configuration of this server, as described in L{hlib.config.servers} documentation.
    """

    self.server_thread		= None
    self.allow_reuse_address	= True

    SocketServer.TCPServer.__init__(self, *args, **kwargs)

    self.pool			= ThreadPool(self, limit = server.max_threads)
    self.app			= server.app

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
      request, client_address = args

      try:
        self.finish_request(request, client_address)
        self.shutdown_request(request)

      # pylint: disable-msg=W0703
      except Exception:
        self.handle_error(request, client_address)
        self.shutdown_request(request)

      finally:
        pool.finish_request()

    hlib.event.trigger('engine.ThreadFinished', None, server = self)

  def process_request(self, request, client_address):
    """
    Called by L{SocketServer} internals for every new request. Its only job is to call server' thread pool's C{add_request} and pass its arguments.

    @type request:		L{socket._socketobject}
    @param request:		Current request' socket.
    @type client_address:	C{tuple}
    @param client_address:	Tuple (C{string}, C{int}) of client' IP address, client' IP port.
    """

    self.pool.add_request(request, client_address)

  def start(self):
    """
    Begin listening on IP port and start accepting requests. Do it in separate (daemon) thread so we can return command to our caller.
    """

    self.server_thread = threading.Thread(target = self.serve_forever, kwargs  = {'poll_interval': 5})
    self.server_thread.daemon = True
    self.server_thread.start()
