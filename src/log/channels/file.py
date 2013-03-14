import hlib.log.channels

class Channel(hlib.log.channels.StreamChannel):
  def __init__(self, path, *args, **kwargs):
    super(Channel, self).__init__(open(path, 'a'), *args, **kwargs)

    self.path		= path

  def close(self):
    self.stream.close()

  def reopen(self):
    self.stream.close()

    self.stream = open(self.path, 'a')
