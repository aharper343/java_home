#!/usr/bin/env python3
import glob
import sys
import os
import argparse

def default_architecture():
  return 'amd64'

def default_location():
  return '/usr/lib/jvm'

def extract_java_home_from_jinfo_line(cmd, line):
  entry = ' '.join(line.rstrip().split(' ')[2:])
  end = os.sep.join(['bin', cmd])
  if entry.endswith(end):
    entry = entry[:-len(end)]
  return entry.rstrip(os.sep)

def extract_value_from_jinfo_line(param, line):
  return line.rstrip()[len(param)+1:]

def load_jinfo(filename, arch):
  with open(filename, 'r') as file:
    jdk = None # We might not find javac
    for line in file.readlines():
      if line.startswith('name='):
        name = extract_value_from_jinfo_line('name', line)
      elif line.startswith('alias='):
        alias = extract_value_from_jinfo_line('alias', line)
      elif line.startswith('priority='):
        priority = extract_value_from_jinfo_line('priority', line)
      elif ' java ' in line:
        jre = extract_java_home_from_jinfo_line('java', line)
      elif ' javac ' in line:
        jdk = extract_java_home_from_jinfo_line('javac', line)
    if jdk == jre:
      jre = None
    return { 'name': name, 'alias': alias, 'priority': priority, 'arch': arch, 'jre': jre, 'jdk': jdk }


def load_all_jinfo(basedir=default_location(), arch=default_architecture()):
  jinfo_list = []
  for filename in glob.glob(f'{basedir}/.*-{arch}.jinfo'):
    jinfo_list.append(load_jinfo(filename, arch))
  return jinfo_list

def jinfo_priority(jinfo):
  return jinfo['priority']

def same_version(version, alias):
  return f'-{version}.' in alias

def find_jinfo(version, arch, jre=False):
  jinfo_list = load_all_jinfo(arch=arch)
  sel_jinfo_list = []
  for jinfo in jinfo_list:
    if (version is None or same_version(version, jinfo['alias'])) and (jre is False or jinfo['jre'] is not None):
      sel_jinfo_list.append(jinfo)
  sel_jinfo_list.sort(key=jinfo_priority)
  return sel_jinfo_list

def list_jvm(version, architecture, jre, latest):
  jinfo_list = find_jinfo(version, architecture, jre)
  if latest and len(jinfo_list) > 1:
    jinfo_list = jinfo_list[len(jinfo_list)- 1:]
  for jinfo in jinfo_list:
    alias = jinfo['alias']
    priority = jinfo['priority']
    arch = jinfo['arch']
    if jre is True:
      java_home = jinfo['jre']
    else:
      java_home = jinfo['jdk']
    print(f'{alias} {priority} {arch} {java_home}', file=sys.stderr)

def get_java_home(version, architecture, jre):
  jinfo_list = find_jinfo(version, architecture, jre)
  if len(jinfo_list) > 0:
    jinfo = jinfo_list[len(jinfo_list) - 1]
    if jre is True:
      java_home = jinfo['jre']
    else:
      java_home = jinfo['jdk']
    return java_home

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='return a value for $JAVA_HOME')
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--version', '-v', type=str, action='store', help='Filters the returned JVMs by the major platform version in "JVMVersion" form. Example versions: "1.5+", or "1.6*".')
  group.add_argument('--latest', '-l', action='store_true', default=False, help='Filters to the most recent JVM.')
#  group.add_argument('--default', '-d', action='store_true', default=False, help='Filters to the current default JVM.')
  parser.add_argument('--verbose', '-V', action='store_true', default=False, help='Prints the matching list of JVMs and architectures to stderr.')
  parser.add_argument('--architecture', '-a', metavar='ARCH', action='store', default=default_architecture(), help='Filters to the provided architecture. Default is ' + default_architecture())
  parser.add_argument('--jre', '-j', action='store_true', default=False, help='Filters to only matching JREs')
  parser.add_argument('--exec', '-e', action='store_true', default=False, help='Executes the command at $JAVA_HOME/bin/<COMMAND> and passes the remaining arguments. Any arguments to select which $JAVA_HOME to use must precede the --exec option.')
  parser.add_argument('cmd', type=str, metavar='COMMAND', nargs='?', help='COMMAND to execute')
  parser.add_argument('cmd_args', type=str, metavar='ARG', nargs='*', help='Arguments for COMMAND')

  cli_args = sys.argv
  cmd_args = None
  for i in range(1, len(cli_args)):
    if cli_args[i] in [ '--exec', '-e']:
      if i + 1 < len(cli_args):
        cmd_args = cli_args[i + 1:]
      else:
        parser.error('--exec/-e must be followed by COMMAND [ARG [ARG ...]]')
        exit(1)
      if i > 1:
        cli_args = cli_args[0: i]
      else:
        cli_args = []
      break
  args = parser.parse_args(cli_args)

  if cmd_args is not None and args.verbose is True:
    parser.error('--exec/-e: not allowed with argument --verbose/-V')
    exit(1)

  if args.verbose is True:
    list_jvm(args.version, args.architecture, args.jre, args.latest)
  elif args.latest is True or args.version is not None:
    java_home = get_java_home(args.version, args.architecture, args.jre)
    if java_home is None:
      exit(1)
    if cmd_args is not None:
      os.putenv('JAVA_HOME', java_home)
      cmd = os.sep.join([java_home, 'bin', cmd_args[0]])
      cmd_args[0] = cmd
      exit(os.execv(cmd, cmd_args))
    else:
      print(java_home)
  else:
    parser.print_usage()
    exit(1)