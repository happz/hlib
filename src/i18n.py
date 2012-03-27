"""
Localization methods

@author:                Milos Prchlik
@contact:               U{happz@happz.cz}
@license:               DPL (U{http://www.php-suit.com/dpl})
"""

import traceback

import hlib.database

# pylint: disable-msg=F0401
import hruntime

class Language(hlib.database.DBObject):
  def __init__(self, name):
    hlib.database.DBObject.__init__(self)

    self.name		= name
    self.tokens		= hlib.database.StringMapping()

    self.hits		= {}
    self.misses		= {}

  def get_unused(self):
    unused = {}

    for key in self.tokens.iterkeys():
      if key in self.hits:
        continue

      unused[key] = True

    return unused

  def gettext(self, name):
    if name in self.tokens:
      self.hits[name] = True
      return self.tokens[name]

    self.misses[name] = True
    return name

class Localization(hlib.database.DBObject):
  """
  Provides methods for translating tokens to into several languages.

  Instantiate with Localization(languages=[lang1, lang2, ...])
  where 'languages' is list of strings, defining languages to be loaded and enabled.
  """

  def __init__(self, languages = None):
    hlib.database.DBObject.__init__(self)

    languages = languages or []

    self.languages	= hlib.database.StringMapping()

    for l in languages:
      self.languages[l] = Language(l)

def gettext(token, **kwargs):
  """
  Translates one token, and replace parameters in result.

  @param token:			Token to translate.
  @type token:			C{string}
  @param kwargs:		Names and values to replace in translated token.
  @type kwargs:			C{dictionary}
  @return:			Translation of token.
  @rtype:			C{string}
  """

  return hruntime.localization.gettext(token) % kwargs
