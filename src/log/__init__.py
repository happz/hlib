import functools
import logging
import sys
import syslog
import time
import traceback

import hlib

# pylint: disable-msg=F0401
import hruntime

hlib.config['log.channels.error'] = None

def make_record(message, params = None, level = None):
  params = {
    'name':     'settlers',
    'level':    level and level or syslog.LOG_ERR,
    'pathname': None,
    'lineno':   None,
    'msg':      message,
    'args':     params and params or tuple(),
    'exc_info': None,
    'func':     None
  }

  return logging.makeLogRecord(params)

def __log(msg, channels):
  for c in channels:
    c.log_message(msg)

def log_access():
  s = [
    ':'.join(hruntime.request.ip),
    '-',
    '-',
    str(hruntime.time),
    '"%s"' % hruntime.request.requested_line,
    str(hruntime.response.status),
    hruntime.response.output_length != None and str(hruntime.response.output_length) or '-',
    '"%s"' % hruntime.request.headers.get('User-Agent', '')
  ]

  s = [
    time.strftime('%d/%m/%Y %H:%M:%S', hruntime.localtime),
    '"%s"' % hruntime.request.requested_line,
    str(hruntime.response.status),
    hruntime.response.output_length != None and str(hruntime.response.output_length) or '-'
  ]

  if hruntime.session != None and hasattr(hruntime.session, 'authenticated') and hasattr(hruntime.session, 'name'):
    s.append('"%s"' % hruntime.session.name)

  __log(' '.join(s), hruntime.app.channels.access)

def log_error(e):
  if e.dont_log == True:
    print >> sys.stderr, 'Skipped exception: \'%s\'' % unicode(e).encode('ascii', 'replace')
    return

  print >> sys.stderr, unicode(e).encode('ascii', 'replace')

  for c in hruntime.app.channels.error:
    c.log_error(e)
