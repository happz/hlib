import formencode

from hlib.tests import *

import hlib.pageable

class ValidatePageTests(TestCase):
  def setUp(self):
    self.V = hlib.pageable.ValidatePage()

  def test_validation(self):
    """
    class ValidatePage(hlib.input.SchemaValidator):
    start  = hlib.input.validator_factory(hlib.input.NotEmpty, hlib.input.Int)
    length = hlib.input.validator_factory(hlib.input.NotEmpty, hlib.input.Int)
    """

    def FAIL(*args, **kwargs):
      EX(formencode.Invalid, self.V.to_python, *args, **kwargs)

    def PASS(*args, **kwargs):
      self.V.to_python(*args, **kwargs)

    FAIL({'start':  0})
    FAIL({'length': 0})
    FAIL({'start': -1, 'length':  0})
    FAIL({'start':  0, 'length': -1})
    FAIL({'start':  0, 'length':  0})
    PASS({'start':  0, 'length': 20})
    PASS({'start': 20, 'length': 20})
