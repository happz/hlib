import hlib.database
from hlib.database import DBObject
import hlib.http

# pylint: disable-msg=F0401
import hruntime

import sys

class Root(DBObject):
  def __init__(self):
    DBObject.__init__(self)

    self.server		= None
    self.localization	= hlib.i18n.Localization(languages = ['cz'])
    self.trumpet	= hlib.database.SimpleMapping()
    self.users		= hlib.database.StringMapping()

class Server(DBObject):
  def __init__(self):
    DBObject.__init__(self)

    self.events		= hlib.database.IndexedMapping()

  online_users		= property(lambda self: hlib.http.session.storage.online_users())

class Event(DBObject):
  def __init__(self, stamp, hidden):
    DBObject.__init__(self)

    self.id		= None
    self.stamp		= stamp
    self.hidden		= hidden

class DummyUser(object):
  def __init__(self, name):
    super(DummyUser, self).__init__()

    self.name		= name

class User(DBObject):
  def __init__(self, name, password, email):
    DBObject.__init__(self)

    self.name		= unicode(name)
    self.password	= unicode(password)
    self.admin		= False
    self.date_format	= '%d/%m/%Y %H:%M:%S'
    self.email		= unicode(email)

    self.cookies	= hlib.database.SimpleMapping()

    self.events		= hlib.database.IndexedMapping()

  is_admin		= property(lambda self: self.admin == True)
  is_online		= property(lambda self: self.name in hlib.http.session.storage.online_users)
