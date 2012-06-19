import pprint
import threading
import time
import types

import hlib
import hlib.event

# pylint: disable-msg=F0401
import hruntime

stats = {
  'Engine': {
    '__fmt__':			{
      'no_fmt':			['Current time', 'Start time']
    },

    'Current time':		lambda s: hruntime.time,
    'Current requests':		0,

    'Start time':		time.time(),
    'Uptime':			lambda s: time.time() - s['Start time'],

    'Total bytes read':		0,
    'Total bytes written':	0,
    'Total requests':		0,
    'Total time':			0,

    'Bytes read/second':	lambda s: s['Total bytes read'] / s['Uptime'](s),
    'Bytes written/second':	lambda s: s['Total bytes written'] / s['Uptime'](s),
    'Bytes read/request':	lambda s: (s['Total requests'] and (s['Total bytes read'] / float(s['Total requests'])) or 0.0),
    'Bytes written/request':	lambda s: (s['Total requests'] and (s['Total bytes written'] / float(s['Total requests'])) or 0.0),
    'Requests/second':		lambda s: float(s['Total requests']) / s['Uptime'](s),

    'Requests':			{}
  }
}

stats_lock = threading.RLock()

def snapshot(d_in):
  with stats_lock:
    d_out = {}

    for k, v in list(d_in.items()):
      if k == '__fmt__':
        pass

      elif isinstance(v, dict):
        v = snapshot(v)

      elif isinstance(v, (list, tuple)):
        v = [snapshot(r) for r in v]

      elif hasattr(v, '__call__'):
        v = v(d_in)

      d_out[k] = v

    return d_out

def iter_collection(collection):
  if type(collection) == types.DictType:
    keys = collection.keys()
  else:
    keys = range(0, len(collection))

  for k in keys:
    d = {'ID': k}
    d.update(collection[k])
    yield d

import hlib.handlers
from hlib.handlers import page, require_login

class Handler(hlib.handlers.GenericHandler):
  def __init__(self, template_name):
    super(Handler, self).__init__()

    self.template_name = template_name

  @require_login
  @page
  def index(self):
    return self.generate(self.template_name, params = {'stats': snapshot(stats)})
