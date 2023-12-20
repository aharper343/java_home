#!/usr/bin/env python3
import glob
import sys
import os
import argparse
import logging

def default_architecture():
  return 'amd64'

def default_location():
  return '/usr/lib/jvm'

def extract_java_home_from_jinfo_line(cmd, line):
  logging.debug('enter: extract_java_jome_from_jinfo_line(%s,%s)', cmd, line)
  entry = ' '.join(line.rstrip().split(' ')[2:])
  end = os.sep.join(['bin', cmd])
  if entry.endswith(end):
    entry = entry[:-len(end)]
  java_home = entry.rstrip(os.sep)
  logging.debug('exit: extract_java_home_from_jinfo_line -> %s', java_home)
  return java_home

def extract_value_from_jinfo_line(param, line):
  return line.rstrip()[len(param)+1:]

def load_jinfo(filename, arch):
  logging.debug('enter: load_jinfo(%s,%s)', filename, arch)
  jinfo = None
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
    jinfo = { 'name': name, 'alias': alias, 'priority': priority, 'arch': arch, 'jre': jre, 'jdk': jdk }
  logging.debug('exit: load_jinfo -> %s', jinfo)
  return jinfo

def load_all_jinfo(basedir=default_location(), arch=default_architecture()):
  logging.debug('enter: load_all_jinfo(%s,%s)', basedir, arch)
  jinfo_list = []
  for filename in glob.glob(f'{basedir}/.*-{arch}.jinfo'):
    jinfo_list.append(load_jinfo(filename, arch))
  logging.debug('exit: load_all_jinfo -> %s', jinfo_list)
  return jinfo_list

def jinfo_priority(jinfo):
  return jinfo['priority']

def same_version(version_requested, version):
  logging.debug('enter: same_version(%s,%s)', version_requested, version)
  prefixes = [ '', '1.']
  same = False
  for requested_prefix in prefixes:
   cmp_version_requested = f'{requested_prefix}{version_requested}'
   for prefix in prefixes:
    cmp_version = f'{prefix}{version}'
    if cmp_version_requested == cmp_version or cmp_version.startswith(f'{cmp_version_requested}.'):
     same = True
     break
   if same:
     break
  logging.debug('exit: same_version -> %s', same)
  return same

def same_version_in_alias(version, alias):
  logging.debug('enter: same_version_in_alias(%s,%s)', version, alias)
  alias_parts = alias.split('-')
  same = False
  if len(alias_parts) > 1:
    same = same_version(version, alias_parts[1])
  logging.debug('same_version version=%s alias=%s alias_version=%s-> %s', version, alias, alias_parts[1], same)
  logging.debug('exit: same_version_in_alias -> %s', same)
  return same

def find_jinfo(version, arch, jre=False):
  logging.debug("enter: find_jinfo(%s,%s,%s)", version, arch, jre)
  jinfo_list = load_all_jinfo(arch=arch)
  sel_jinfo_list = []
  for jinfo in jinfo_list:
    if (version is None or same_version_in_alias(version, jinfo['alias'])) and (jre is False or jinfo['jre'] is not None):
      sel_jinfo_list.append(jinfo)
  sel_jinfo_list.sort(key=jinfo_priority)
  logging.debug('exit: find_jinfo -> %s', sel_jinfo_list)
  return sel_jinfo_list


def list_jvm(version, arch, jre, latest):
  logging.debug('enter: list_jvm(%s,%s,%s,%s)', version, arch, jre, latest)
  jinfo_list = find_jinfo(version, arch, jre)
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
  logging.debug('exit: list_jvm')

def get_java_home(version, arch, jre):
  logging.debug('enter: get_java_home(%s,%s,%s)', version, arch, jre)
  jinfo_list = find_jinfo(version, arch, jre)
  java_home = None
  if len(jinfo_list) > 0:
    jinfo = jinfo_list[len(jinfo_list) - 1]
    if jre is True:
      java_home = jinfo['jre']
    else:
      java_home = jinfo['jdk']
  logging.debug('exit: get_java_home -> %s', java_home)
  return java_home

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='return a value for $JAVA_HOME')
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--version', '-v', type=str, action='store', help='Filters the returned JVMs by the major platform version in "JVMVersion" form. Example versions: "1.5+", or "1.6*".')
  group.add_argument('--latest', '-l', action='store_true', default=False, help='Filters to the most recent JVM.')
  parser.add_argument('--debug', '-D', action='store_true', default=False, help='Enables debug logging')
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

  if args.debug is True:
    logging.basicConfig(level=logging.DEBUG)

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