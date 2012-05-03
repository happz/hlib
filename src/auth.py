"""
Authentication and authorization functions

@author:                Milos Prchlik
@contact:               U{happz@happz.cz}
@license:               DPL (U{http://www.php-suit.com/dpl})
"""

import hlib
import hlib.datalayer
import hlib.event
import hlib.http
import hlib.http.session

# pylint: disable-msg=F0401
import hruntime

def refresh_session():
  """
  When called, sets some default values based on session - current user and his
  preffered language.
  """

  hruntime.response.headers['Cache-Control'] = 'must-revalidate, no-cache, no-store'

  hruntime.user = hruntime.dbroot.users[hruntime.session.name]
  hruntime.i18n = hruntime.dbroot.localization.languages['cz']

def start_session(user = None, tainted = False):
  """
  Start new session.

  @type user:			L{lib.datalayer.User}
  @param user:			If set, save its id and name into session.
  @type tainted:		C{bool}
  @param tainted:		If not C{False}, L{lib.datalayer.User} is expected
                                and its id is saved to session.
  """

  hruntime.session.refresh_sid()

  hruntime.session.authenticated = True
  hruntime.session.name = user.name

  if tainted != False:
    # pylint: disable-msg=E1101,E1103
    hruntime.session.tainted = tainted.name

  elif hasattr(hruntime.session, 'tainted'):
    del hruntime.session.tainted

  refresh_session()

def check_session(redirect_to_login = True):
  """
  Check if current session contains authenticated user record - if not, redirect request to
  login page.

  @raise hlib.http.Redirect:	Raised when there is no session started, redirect user to login page.
  """

  if hruntime.request.is_authenticated == False:
    if redirect_to_login == True:
      raise hlib.http.Redirect('/login/')

    return

  refresh_session()

  hruntime.app.sessions.purge()

def logout(trigger_event = True):
  """
  Mark session as not authenticated and redirect to login page.
  """

  if trigger_event == True:
    hlib.event.trigger('system.UserLoggedOut', hruntime.dbroot.server, user = hruntime.user)

  hruntime.session.destroy()
  hruntime.session = None

  raise hlib.http.Redirect('/login/')
