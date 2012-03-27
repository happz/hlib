"""
Methods for formating text output

@author:	                Milos Prchlik
@contact:       	        U{happz@happz.cz}
@license:               	DPL (U{http://www.php-suit.com/dpl})
"""

import hlib

import bbcode

def _do_tagize(text):
  return bbcode.bb2xhtml(text)

# pylint: disable-msg=W0613
def tagize(text, mid = None):
  """
  Process tags in text.

  @param text:			Text to be processed.
  @type text:			C{string}
  @param mid:			If set, result can be stored in cache using C{mid} as key.
  @type mid:			C{hashable}
  """

  return _do_tagize(text)
