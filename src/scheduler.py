import datetime
import threading
import time

class __AllMatch(set):
  def __contains__(self, item):
    return True

allMatch = __AllMatch()

class Task(object):
  def __init__(self, name, callback, min = allMatch, hour = allMatch, day = allMatch, month = allMatch, dow = allMatch, *args, **kwargs):
    super(Task, self).__init__()

    self.name = name

    self.callback = callback
    self.args = args
    self.kwargs = kwargs

    def __conv_to_set(obj):
      if isinstance(obj, (int, long)):
        return set([obj])
      if not isinstance(obj, set):
        obj = set(obj)
      return obj

    self.mins = __conv_to_set(min)
    self.hours = __conv_to_set(hour)
    self.days = __conv_to_set(day)
    self.months = __conv_to_set(month)
    self.dow = __conv_to_set(dow)

  def matchtime(self, t):
    return (    (t.minute in self.mins)
            and (t.hour in self.hours)
            and (t.day in self.days)
            and (t.month in self.months)
            and (t.weekday() in self.dow))

  def run(self, t):
    if not self.matchtime(t):
      return

    print '%s time matched' % self.name

    self.callback(*self.args, **self.kwargs)

class SchedulerThread(threading.Thread):
  def __init__(self, engine, *args, **kwargs):
    threading.Thread.__init__(self, *args, **kwargs)

    self.daemon = True
    self.engine = engine

    self.lock = threading.RLock()
    self.tasks = {}

  def add_task(self, task):
    with self.lock:
      self.tasks[task.name] = task

  def remove_task(self, task):
    with self.lock:
      del self.tasks[task.name]

  def run(self):
    while True:
      t = datetime.datetime(*datetime.datetime.now().timetuple()[:5])

      with self.lock:
        for task in self.tasks.values():
          task.run(t)

      t += datetime.timedelta(minutes = 1)
      while datetime.datetime.now() < t:
        time.sleep((t - datetime.datetime.now()).seconds)
