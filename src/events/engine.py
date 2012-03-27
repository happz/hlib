from hlib.events import Event

class ThreadEvent(Event):
  dont_store = True

  def __init__(self, server, *args, **kwargs):
    Event.__init__(self, *args, **kwargs)

    self.server		= server

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

import hlib

hlib.register_event(Started)
hlib.register_event(Halted)
hlib.register_event(ThreadStarted)
hlib.register_event(ThreadFinished)
hlib.register_event(RequestConnected)
hlib.register_event(RequestAccepted)
hlib.register_event(RequestStarted)
hlib.register_event(RequestFinished)
