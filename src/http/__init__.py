import hlib.error

# pylint: disable-msg=F0401
import hruntime

HTTP_CODES = {
  # 1xx - Informational
  # 2xx - Successful
  200:          'OK',
  201:          'Created',
  202:          'Accepted',
  203:          'Non-Authoritative Information',
  204:          'No Content',
  205:          'Reset Content',
  206:          'Partial Content',
  # 3xx - Redirection
  300:          'Multiple Choices',
  301:          'Moved Permanently',
  302:          'Found',
  303:          'See Other',
  304:          'Not Modified',
  305:          'Use Proxy',
  307:          'Temporary Redirect',
  # 4xx - Client error
  400:          'Bad Request',
  401:          'Unauthorized',
  402:          'Payment Required',
  403:          'Forbidden',
  404:          'Not Found',
  405:          'Method Not Allowed',
  406:          'Not Acceptable',
  407:          'Proxy Authentication Required',
  408:          'Request Timeout',
  409:          'Conflict',
  410:          'Gone',
  411:          'Length Required',
  412:          'Precondition Failed',
  413:          'Request Entity Too Large',
  414:          'Request-URI Too Long',
}

class HTTPError(hlib.error.Error):
  def __init__(self, *args, **kwargs):
    super(HTTPError, self).__init__(*args, **kwargs)

    self.requested_url = hruntime.request.requested

class NotFound(HTTPError):
  pass

class Redirect(HTTPError):
  def __init__(self, location, *args, **kwargs):
    super(Redirect, self).__init__(*args, **kwargs)

    self.location = location

class Prohibited(HTTPError):
  pass

class UnknownMethod(HTTPError):
  pass
