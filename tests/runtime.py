from hlib.tests import *

import time

import hlib.runtime

import hruntime

class RuntimeTests(TestCase):
  def test_clean(self):
    hruntime.user = True
    hruntime.dont_commit = True
    hruntime.ui_form = True
    hruntime.time = True

    hruntime.clean()

    NONE(hruntime.user)
    F(hruntime.dont_commit)
    NONE(hruntime.ui_form)
    ANY(hruntime.time)

  def test_reset(self):
    for p in hruntime.RESET_PROPERTIES:
      setattr(hruntime, p, True)
    hruntime.reset_locals()
    for p in hruntime.RESET_PROPERTIES:
      if p in ('time', 'localtime'):
        ANY(getattr(hruntime, p))
      else:
        NONE(getattr(hruntime, p))

  @SKIP
  def test_time(self):
    stamp = hruntime.time
    time.sleep(2)
    EQ(stamp, hruntime.time)
    hruntime.time = None
    time.sleep(2)
    NEQ(stamp, hruntime.time)

  def test_localtime(self):
    stamp = hruntime.time
    EQ(time.localtime(stamp), hruntime.localtime)
