import hlib.log.channels

class Channel(hlib.log.channels.StreamChannel):
  def __init__(self, path, *args, **kwargs):
    super(Channel, self).__init__(open(path, 'a'), *args, **kwargs)
