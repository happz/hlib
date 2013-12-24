__author__ = 'Milos Prchlik'
__copyright__ = 'Copyright 2010 - 2013, Milos Prchlik'
__contact__ = 'happz@happz.cz'
__license__ = 'http://www.php-suit.com/dpl'

from hlib.events import Event

class ThreadEvent(Event):
  dont_store = True

  def __init__(self, server, thread, *args, **kwargs):
    Event.__init__(self, *args, **kwargs)

    self.server = server
    self.thread = thread

class Started(Event):
  dont_store = True

class Halted(Event):
  dont_store = True

class ThreadStarted(ThreadEvent):
  pass

class ThreadFinished(ThreadEvent):
  pass

class RequestConnected(Event):
  dont_store = True

class RequestAccepted(Event):
  dont_store = True

class RequestStarted(Event):
  dont_store = True

class RequestFinished(Event):
  dont_store = True

class RequestClosed(Event):
  dont_store = True

Started.register()
Halted.register()
ThreadStarted.register()
ThreadFinished.register()
RequestConnected.register()
RequestAccepted.register()
RequestStarted.register()
RequestFinished.register()
RequestClosed.register()
