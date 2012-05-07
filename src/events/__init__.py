"""
System and game events

@author:			Milos Prchlik
@contact:			U{happz@happz.cz}
@license:			DPL (U{http://www.php-suit.com/dpl})
"""

# pylint: disable-msg=R0401

import hlib.datalayer

# pylint: disable-msg=F0401
import hruntime

def ename(cls):
  return '.'.join([] + (cls.__module__.startswith('hlib') and cls.__module__.split('.')[2:] or cls.__module__.split('.')[1:]) + [cls.__name__])

class Event(hlib.datalayer.Event):
  """
  Baseclass for all possible events.
  """

  dont_store	= False

  def __init__(self, hidden = False):
    hlib.datalayer.Event.__init__(self, hruntime.time, hidden)

  def to_api(self):
    return {
      'id':		self.id,
      'stamp':		self.stamp,
      'hidden':		self.hidden,
      'ename':		ename(self.__class__)
    }
