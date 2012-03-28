import hlib

# pylint: disable-msg=F0401
import hruntime

hlib.config.cookies = hlib.Config()
hlib.config.cookies.default_max_age = 604800		# 1 week

class Cookie(object):
  def __init__(self, name, value = None, max_age = None, path = None, server = None):
    super(Cookie, self).__init__()

    self.server			= server
    self.name			= name
    self.value			= value
    self.max_age		= max_age or (self.server and hasattr(self.server, 'cookie_max_age') and self.server.cookie_max_age or hlib.config.cookies.default_max_age)
    self.path			= path or '/'

  def set(self):
    hruntime.response.cookies[self.name] = self

  def delete(self):
    self.value			= '_deleted_'
    self.max_age		= 0

    self.set()
