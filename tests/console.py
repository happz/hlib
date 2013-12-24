from hlib.tests import *

import StringIO
import sys

import hlib.console

class EchoCommand(hlib.console.Command):
  def __init__(self, console, parser):
    super(EchoCommand, self).__init__(console, parser)

    self.parser.add_argument('--ping', action = 'store', dest = 'ping', required = True)

  def handler(self, args):
    return {'pong': args.ping}

class DummyEngine(object):
  def stop(self):
    pass

class ConsoleTests(TestCase):
  def test_sanity(self):
    cin = StringIO.StringIO('echo --ping foo\nsys --quit\n')
    cout = StringIO.StringIO()

    console = hlib.console.Console(None, DummyEngine(), cin, cout)
    console.register_command('echo', EchoCommand)
    console.cmdloop()

    EQ(cout.getvalue(), """console# {
    "pong": "foo",
    "status": "OK"
}
console# {
    "status": "OK"
}
""")

  def test_missing_arg(self):
    cin = StringIO.StringIO('echo\nsys --quit\n')
    cout = StringIO.StringIO()

    console = hlib.console.Console(None, DummyEngine(), cin, cout)
    console.register_command('echo', EchoCommand)
    console.cmdloop()

    EQ(cin.getvalue(), """echo
sys --quit
""")
    EQ(cout.getvalue(), """console# {
    "message": "argument --ping is required",
    "status": "ERROR"
}
console# {
    "status": "OK"
}
""")
