# pylint: disable-msg=F0401
import hruntime

class Cookie(object):
  def __init__(self, name, value = None, expires = None, path = None):
    super(Cookie, self).__init__()

    self.name			= name
    self.value			= value
    self.expires		= expires or 'Sun, 20 Feb 2013 20:47:11 GMT'
    self.path			= path or '/'

  def set(self):
    hruntime.response.cookies[self.name] = self

  def delete(self):
    self.value			= '_deleted_'
    self.expires		= 0

    self.set()
