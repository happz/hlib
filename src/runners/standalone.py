import getopt
import sys

import hlib.runners

config_file = None

def usage():
  print sys.argv[0] + """ <options>

where options can be:

  -h              Print this message and quit
  -c config_file  Specify different path to config file

"""
  sys.exit(0)

def main(root, config_defaults, on_app_config):
  optlist, args = getopt.getopt(sys.argv[1:], 'c:h')

  for o in optlist:
    if o[0] == '-h':
      usage()

    elif o[0] == '-c':
      config_file = o[1]

    runner = hlib.runners.Runner(config_file, root, config_defaults = config_defaults, on_app_config = on_app_config)
    runner.run()
