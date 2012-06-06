import types

# pylint: disable-msg=F0401
import hruntime

class Channel(object):
  def do_log_message(self, msg):
    pass

  def log_message(self, record):
    msg = type(record) not in types.StringTypes and (record.msg % record.args) or record

    self.do_log_message(msg)

  def log_error(self, error):
    pass

class StreamChannel(Channel):
  def __init__(self, stream, *args, **kwargs):
    super(StreamChannel, self).__init__(*args, **kwargs)

    self.stream		= stream

  def do_log_message(self, msg):
    print >> self.stream, msg
    self.stream.flush()

  def log_error(self, error):
    import hlib.ui.templates.Mako

    t = hlib.ui.templates.Mako.Template('hlib_error_plain.mako', indent = False, app = hruntime.app).load()
    self.do_log_message(t.render(params = {'error': error}).strip())
