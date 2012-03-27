import sys

import hlib.log.channels

class Channel(hlib.log.channels.StreamChannel):
  def __init__(self, *args, **kwargs):
    super(Channel, self).__init__(sys.stdout, *args, **kwargs)
