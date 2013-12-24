from hlib.tests import *

import hlib.events
from hlib.events import Event, Hook, trigger

class DummyEvent(Event):
  dont_store = True

class DummyCallback(object):
  def __init__(self):
    self.b = False

  def callback_to_true(self, event):
    self.b = True

class EventTests(TestCase):
  def test_sanity(self):
    callback = DummyCallback()
    F(callback.b)

    DummyEvent.register()
    T(DummyEvent.is_registered())

    hook = Hook('events.DummyEvent', callback.callback_to_true)
    T(hook.is_registered())

    trigger('events.DummyEvent', None)
    T(callback.b)

    hook.unregister()
    F(hook.is_registered())

    DummyEvent.unregister()
    F(DummyEvent.is_registered())
