from hlib.tests import *

import hlib.datalayer

class UserTests(hlib.tests.TestCase):
  _users = {}

  def user(self, name, password = None, email = None):
    password = password or 'password'
    email = email or 'email@email.cz'

    users = self.__class__._users

    if name not in users:
      users[name] = hlib.datalayer.User(name, password, email)

    return users[name]

  def test_create(self):
    U = self.user('foo', password = 'bar', email = 'baz')

    EQ('foo', U.name)
    EQ('bar', U.password)
    EQ('baz', U.email)

  def test_eq(self):
    u1 = self.user('A')
    u2 = self.user('B')
    u3 = hlib.datalayer.User('A', 'different password', 'different mail')

    NEQ(u1, u2)
    NEQ(u2, u3)
    EQ(u1, u3)

  def test_api_tokens(self):
    U = self.user('A')

    LEQ(U.api_tokens, 0)
    U.api_tokens.append('foobar')
    IN('foobar', U.api_tokens)
    LEQ(U.api_tokens, 1)
    U.reset_api_tokens()
    NIN('foobar', U.api_tokens)
    LEQ(U.api_tokens, 0)
