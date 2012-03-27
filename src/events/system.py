"""
System-wide events.

@author:                        Milos Prchlik
@contact:                       U{happz@happz.cz}
@license:                       DPL (U{http://www.php-suit.com/dpl})
"""

from hlib.events import Event

class UserEvent(Event):
  def __init__(self, user = None, **kwargs):
    Event.__init__(self, **kwargs)

    self.user		= user

class UserLoggedIn(UserEvent):
  dont_store = True

class UserLoggedOut(UserEvent):
  dont_store = True

import hlib

hlib.register_event(UserLoggedIn)
hlib.register_event(UserLoggedOut)
