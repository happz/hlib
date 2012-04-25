"""
Basic exception tree

@author:                Milos Prchlik
@contact:               U{happz@happz.cz}
@license:               DPL (U{http://www.php-suit.com/dpl})
"""

import logging
import sys
import syslog
import thread
import time
import traceback
import types

import hlib
import hlib.log

# pylint: disable-msg=F0401
import hruntime

class Error(Exception):
  """
  Top-level exception
  """

  def __init__(self, msg = None, params = None, exception = None, exc_info = None, http_status = 500, reply_status = 0, invalid_field = None, **kwargs):
    """
    @type msg:			C{string}
    @param msg:			Optional text of exception
    @type params:		C{dictionary}
    @param params:		Optional params to replace in exception message
    """

    super(Error, self).__init__()

    self.msg       = msg
    self.params    = params or {}
    self.exception = exception
    self.exc_info  = exc_info
    self.http_status = http_status
    self.reply_status = reply_status
    self.invalid_field = invalid_field

    for k, v in kwargs.iteritems():
      setattr(self, k, v)

    if self.exc_info:
      self.tb = traceback.extract_tb(self.exc_info[2])

    else:
      self.tb = traceback.extract_stack()[0:-1]

  name			= property(lambda self: self.exc_info and self.exc_info[0].__name__ or '*Unknown*')
  # pylint: disable-msg=W0703
  message		= property(lambda self: self.msg.format(**self.params))
  file		 	= property(lambda self: self.tb[-1][0])
  line			= property(lambda self: self.tb[-1][1])
  code			= property(lambda self: '%i. %s' % (self.line, open(self.file, 'r').readlines()[self.line]))
  log_record		= property(lambda self: logging.makeLogRecord({'name': 'settlers', 'level': syslog.LOG_ERR, 'pathname': self.file, 'lineno': self.line, 'msg': self.msg, 'args': self.params, 'exc_info': self.exc_info, 'func': None}))

  def __str__(self):
    return self.msg % self.params

  def __unicode__(self):
    return unicode(self.msg) % self.params

def error_from_exception(e):
  if len(e.args) != 0:
    msg = ':'.join([unicode(i).encode('ascii', 'replace') for i in e.args])

  elif len(e.message) != 0:
    msg = e.message

  else:
    # pylint: disable-msg=W0212
    msg = e._exceptions[0][1].args[0]

  return Error(msg = msg, params = None, reply_status = 500, exception = e, exc_info = sys.exc_info())

ErrorByException = error_from_exception

class DieError(Error):
  """
  "Kill-me-now" exception - we want to exit and rollback db changes and we want it now. Nothing
  less, nothing more.
  """

  def __init__(self):
    """
    No arguments needed, we just hate this code.
    """

    super(DieError, self).__init__(msg = 'Die! Die! Die!')

class UnimplementedError(Error):
  """
  Exception that signals some function is left unimplemented yet.
  """

  @staticmethod
  def function_name(obj, frames):
    """
    Create a string naming the function n frames up on the stack.

    @todo:			DocString
    """

    # pylint: disable-msg=W0212
    fr = sys._getframe(frames + 1)
    co = fr.f_code
    return "%s.%s" % (obj.__class__, co.co_name)

  def __init__(self, obj = None):
    """
    @type obj:			C{callable object}
    @param obj:			Unimplemented function wrapper that called this function.
    """

    super(UnimplementedError, self).__init__('Unimplemented abstract method: %(method)s', params = {'method': UnimplementedError.function_name(obj, 2)})

class UnknownError(Error):
  pass

class TemporarilyDisabled(Error):
  pass

class InvalidInputError(Error):
  pass

class AccessDeniedError(Error):
  pass
