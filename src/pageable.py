import hlib.api
import hlib.input

class ValidatePage(hlib.input.SchemaValidator):
  start = hlib.input.validator_factory(hlib.input.NotEmpty, hlib.input.Int)
  length = hlib.input.validator_factory(hlib.input.NotEmpty, hlib.input.Int)

class ApiPageable(hlib.api.ApiJSON):
  def __init__(self):
    super(ApiPageable, self).__init__(['cnt_total', 'cnt_display', 'records'])

    self.cnt_total              = 0
    self.cnt_display            = 0
    self.records                = []

class Pageable(object):
  def __init__(self, default_length = None):
    super(Pageable, self).__init__()

    self.default_length = default_length if default_length != None else 20

  def record_to_api(self, record):
    return None

  def get_records(self, start, length):
    return ([], 0)
    
  def get_page(self, start = None, length = None):
    start = start if start != None else 0
    length = length if length != None else self.default_length

    reply = ApiPageable()

    records, cnt_total = self.get_records(start, length)

    for record in records:
      reply.records.append(self.record_to_api(record))

    reply.cnt_total = cnt_total
    reply.cnt_display = len(records)

    return reply
