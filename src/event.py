"""
System and game events

@author:                Milos Prchlik
@contact:               U{happz@happz.cz}
@license:               DPL (U{http://www.php-suit.com/dpl})
"""

import collections

import hlib
import hlib.database

__all__ = ['trigger', 'Hook']

_HOOKS = {
}

class Hook(object):
  def __init__(self, event, name, callback, post = True, args = None, kwargs = None):
    super(Hook, self).__init__()

    self.event		= event
    self.name           = name
    self.callback       = callback
    self.post		= post
    self.args           = args or []
    self.kwargs         = kwargs or {}

    if event not in _HOOKS:
      _HOOKS[event] = collections.OrderedDict()

    _HOOKS[event][name] = self

  def __call__(self, event):
    _args = self.args + [event]

    # pylint: disable-msg=W0142
    return self.callback(*_args, **self.kwargs)

  def remove(self):
    del _HOOKS[self.event][self.name]

def trigger(name, holder, post = True, **kwargs):
  """
  Raise new event.

  @type name:			C{string}
  @param name:			Events name
  @type kwargs:			C{dictionary}
  @param kwargs:		Arguments to pass to event's constructor
  @rtype:			L{hlib.events.Event}
  @return:			Newly created event object
  """

  # pylint: disable-msg=W0142
  e = hlib.EVENTS[name]
  e = e(**kwargs)
  if e.dont_store != True:
    holder.events.push(e)

  if name in _HOOKS:
    for hook in _HOOKS[name].itervalues():
      if hook.post == post:
        hook(e)

import hlib.events.system
import hlib.events.engine
