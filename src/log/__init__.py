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

def log_msg(msg, channels):
  for c in channels:
    c.log_message(msg)

def log_params():
  return {
    'tid':			hruntime.tid,
    'stamp':			hruntime.localtime,
    'date':			time.strftime('%d/%m/%Y', hruntime.localtime),
    'time':			time.strftime('%H:%M:%S', hruntime.localtime),
    'request_line':		hruntime.request.requested_line,
    'request_ip':		hlib.ips_to_str(hruntime.request.ips),
    'request_user':		hruntime.session.name if hruntime.session != None and hasattr(hruntime.session, 'authenticated') and hasattr(hruntime.session, 'name') else '-',
    'request_agent':		hruntime.request.headers.get('User-Agent', '-'),
    'response_status':		hruntime.response.status,
    'response_length':		hruntime.response.output_length != None and hruntime.response.output_length or 0,
    'session_id':		hruntime.session.sid if hruntime.session != None else None
  }

def log_access():
  params = log_params()

  log_msg(hruntime.app.config['log.access.format'].format(**params), hruntime.app.channels.access)

def log_error(e):
  if e.dont_log == True:
    print >> sys.stderr, 'Skipped exception: \'%s\'' % unicode(e).encode('ascii', 'replace')
    return

  print >> sys.stderr, unicode(e).encode('ascii', 'replace')

  for c in hruntime.app.channels.error:
    c.log_error(e)

def log_dbg(msg):
  log_msg('%s - %s' % (hruntime.tid, msg), [hlib.config['log.channels.error']])
