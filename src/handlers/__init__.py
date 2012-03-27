import sys
import types
import urllib

import hlib
import hlib.error
import hlib.log
import hlib.server
import hlib.ui.templates.Mako

# pylint: disable-msg=F0401
import hlib.http

import hruntime

__all__ = ['tag_fn', 'prohibited', 'require_login', 'require_admin', 'require_write',
           'page',
           'GenericHandler']

def tag_fn_prep(fn):
  if not hasattr(fn, 'config'):
    setattr(fn, 'config', dict())

def tag_fn(fn, tag, value):
  tag_fn_prep(fn)

  if tag not in fn.config:
    fn.config[tag] = value

  return fn

def tag_fn_check(fn, tag, default):
  if not hasattr(fn, 'config'):
    return default

  return fn.config.get(tag, default)

def prohibited(f):
  return tag_fn(f, 'prohibited', True)

def require_login(fn):
  return tag_fn(fn, 'require_login', True)

def require_admin(f):
  return tag_fn(f, 'require_admin', True)

def require_write(f):
  return tag_fn(f, 'require_write', True)

def page(fn):
  return tag_fn(fn, 'page', True)

def run_page_handler():
  try:
    hlib.input.validate()

    return hruntime.request.handler(**hruntime.request.params)

  except hlib.http.Redirect, e:
    hruntime.dont_commit = True
    raise e

  except Exception, e:
    print e
    hruntime.dont_commit = True

    if not isinstance(e, hlib.error.Error):
      e = hlib.error.ErrorByException(e)

    hlib.log.log_error(e)

    return ''

def enable_write():
  require_write(hruntime.request.handler)

def gettext(s):
  return hlib.i18n.gettext(s).encode('ascii', 'xmlcharrefreplace')

def prepare_template_params(params = None):
  real_params = GenericHandler.PARAMS.copy()
  params = params or {}
  real_params.update(params)

  real_params['root']     = hruntime.root
  real_params['user']     = hruntime.user
  real_params['server']   = hruntime.server
  real_params['_']        = gettext
  real_params['title']    = hruntime.app.title
  real_params['basepath'] = hruntime.request.base
  
  real_params['_q']       = urllib.quote

  return real_params
  
class GenericHandler(object):
  PARAMS = {}

  def __init__(self):
    super(GenericHandler, self).__init__()

  def generate(self, template, params = None):
    params = prepare_template_params(params = params)

    params['handler'] = self

    indent = True
    if hruntime.user != None and hruntime.user.is_admin:
      indent = True

    t = hlib.ui.templates.Mako.Template(template, indent = indent).load()
    return t.render(params = params)
