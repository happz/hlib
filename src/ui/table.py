import collections

class TableHeader(object):
  # type - field type for datatables
  # key - use this to sort lists, fn(x)
  # label - field header
  # pylint: disable-msg=W0622
  def __init__(self, type = None, key = None, label = None):
    super(TableHeader, self).__init__()

    self.type   = type or 'string'
    self.key    = key
    self.label  = label or None

  def sort_by(self, items, reverse):
    return sorted(items, key = self.key, reversed = reverse)

class Table(object):
  def __init__(self, *headers, **kwargs):
    # pylint: disable-msg=W0613
    super(Table, self).__init__()

    self.headers = collections.OrderedDict()
    for h in headers:
      self.headers[h[0]] = h[1]
