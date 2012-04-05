"""
Methods for formating text output.
"""

__author__              = 'Milos Prchlik'
__copyright__           = 'Copyright 2010 - 2012, Milos Prchlik'
__contact__             = 'happz@happz.cz'
__license__             = 'http://www.php-suit.com/dpl'

try:
  import bbcode
  __do_tagize = bbcode.bb2xhtml

except ImportError:
  __do_tagize = lambda text: text

import hlib

def _do_tagize(text):
  return bbcode.bb2xhtml(text)

# pylint: disable-msg=W0613
def tagize(text):
  """
  Process tags in text.

  @type text:			C{string}
  @param text:			Text to be processed.
  """

  return __do_tagize(text)
