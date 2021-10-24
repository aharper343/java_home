#!/usr/bin/env python3
import glob
import sys
import os

def default_architecture():
  return 'amd64'

def extract_java_home_from_jinfo_line(cmd, line):
  entry = ' '.join(line.rstrip().split(' ')[2:])
  end = os.sep.join(['bin', cmd])
  if entry.endswith(end):
    entry = entry[:-len(end)]
  return entry

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


def load_all_jinfo(basedir='/usr/lib/jvm',arch=default_architecture()):
  jinfo_list = []
  for filename in glob.glob(f'{basedir}/.*-{arch}.jinfo'):
    jinfo_list.append(load_jinfo(filename, arch))
  return jinfo_list

def jinfo_priority(jinfo):
  return jinfo['priority']

def find_jinfo(version, jre=False, arch='amd64'):
  jinfo_list = load_all_jinfo(arch=arch)
  sel_jinfo_list = []
  for jinfo in jinfo_list:
    if (version is None or f'-{version}.' in jinfo['alias']) and (jre is False or jinfo['jre'] is not None):
      sel_jinfo_list.append(jinfo)
  sel_jinfo_list.sort(key=jinfo_priority)
  return sel_jinfo_list

def list_jvm(version, jre):
  jinfo_list = find_jinfo(version, jre)
  for jinfo in jinfo_list:
    alias = jinfo['alias']
    priority = jinfo['priority']
    arch = jinfo['arch']
    if jre is True:
      java_home = jinfo['jre']
    else:
      java_home = jinfo['jdk']
    print(f'{alias} {priority} {arch} {java_home}', file=sys.stderr)

def get_java_home(version, jre):
  jinfo_list = find_jinfo(version, jre)
  if len(jinfo_list) > 0:
    jinfo = jinfo_list[len(jinfo_list) - 1]
    if jre is True:
      java_home = jinfo['jre']
    else:
      java_home = jinfo['jdk']
    return java_home

def print_help():
  print(f'{sys.argv[0]} - return a value for $JAVA_HOME')
  print('\t-h or --help : This message')
  print('\t-v or --version  VERSION\n\t\tFilters the returned JVMs by the major platform version in "JVMVersion" form.\n\t\tExample versions: "1.5+", or "1.6*".')
  print('\t-V or --verbose\n\t\tPrints the matching list of JVMs and architectures to stderr.')
  print('\t-e or --exec COMMAND [ARG ..]\n\t\tExecutes the command at $JAVA_HOME/bin/<command> and passes the remaining arguments.\n\t\tAny arguments to select which $JAVA_HOME to use must precede the --exec option.')
  print('\t-j or --jre\n\t\tFilters to only matching JREs')
  print('\t-l or --latest\n\t\tFilters to the most recent JVM.')
  print('\tNOTE: -v or --version VERSION and -l --latest cannot be used at the same tine')
  print('\t      -e or --exec COMMAND [ARG ...] must be used with either\n\t\t-v or --version VERSION\n\t\t-l or --latest')
  exit(0)

def print_usage(file):
  print(f'Usage: {sys.argv[0]}: [--help/-h] [--version/-v VERSION] [--latest/-l] [--verbose/-V] [--jre/-j] [--exec COMMAMD [ARG ...]]', file=file)

def print_error_and_exit(message):
  print_usage(sys.stderr)
  print(f'{sys.argv[0]}: error: {message}', file=sys.stderr)
  exit(1)

def arg_check_and_exit(arg, other_arg, is_set):
  if is_set:
    print_error_and_exit(f'{arg} cannot be set when {other_arg} is set')

if __name__ == '__main__':
  exec = False
  verbose = False
  latest = False
  version = None
  jre = False
  args = []
  i = 1
  while i < len(sys.argv):
    arg = sys.argv[i]
    if arg == '--exec' or arg == '-e':
      my_arg = '--exec/-e'
      if exec is False:
        arg_check_and_exit(my_arg, '--verbose/-V', verbose)
        if latest is True or version is not None:
          i = i + 1
          if i >= len(sys.argv):
            print_error_and_exit(f'{my_arg} must be followed by COMMAND')
          exec = True
          args = sys.argv[i:]
          break
        else:
          print_error_and_exit(f'{my_arg} must appear after --version/-v VERSION or --latest/-l')
      else:
        print_error_and_exit(f'{my_arg} can appear only once')
    elif arg == '--verbose' or arg == '-V':
      my_arg = '--verbose/-V'
      if verbose is False:
        verbose = True
      else:
        print_error_and_exit(f'{my_arg} can appear only once')
    elif arg == '--latest' or arg == '-l':
      my_arg = '--latest/-l'
      if latest is False:
        arg_check_and_exit(f'{my_arg}','--version/-v VERSION', version is not None)
        latest = True
      else:
        print_error_and_exit(f'{my_arg} can appear only once')
    elif arg == '--version' or arg == '-v':
      my_arg = '--version/-v VERSION'
      if version is None:
        arg_check_and_exit(f'{my_arg}','--latest/-l', latest)
        i = i + 1
        if i >= len(sys.argv):
          print_error_and_exit(f'{my_arg} must be followed by VERSION')
        version = sys.argv[i]
      else:
        print_error_and_exit(f'{my_arg} can appear only once')
    elif arg == '--jre' or arg == '-j':
      jre = True
    elif arg == '--help' or arg == '-h':
      print_help()
    else:
      print_error_and_exit(f'{arg} is unexpected')
    i = i + 1

  if verbose is True:
    list_jvm(version, jre)
  elif latest is True or version is not None:
    java_home = get_java_home(version, jre)
    if java_home is None:
      exit(1)
    if exec is True:
      os.putenv('JAVA_HOME', java_home)
      cmd = os.sep.join([java_home, 'bin', args[0]])
      exit(os.execv(cmd, args))
    else:
      print(java_home)
  else:
    print_usage(sys.stderr)
    exit(1) 