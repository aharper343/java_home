# java_home

An implementation for Ubuntu of `/usr/libexec/java_home` from the Apple Mac

## Approach

java_home.py reads the `.jinfo` files at `/usr/lib/jvm` the following elements of the
`.jinfo` file are loaded:

```jinfo
name=java-17-openjdk-amd64
alias=java-1.17.0-openjdk-amd64
priority=1711
...
```

It then looks for the location of the commands `java` to determine if its at a JRE location
and `javac` for the JDK location. Examples for those `.jinfo` entries are:

```jinfo
...
hl java /usr/lib/jvm/java-17-openjdk-amd64/bin/java
...
jdkhl javac /usr/lib/jvm/java-17-openjdk-amd64/bin/javac
...
```

The version matching is currently **exact** match with support still needed for "JVMVersion"
version matching. i.e. 1.8+ 1.11*

## Usage

```plaintext
usage: java_home [-h] [--version VERSION | --latest] [--verbose]
                 [--architecture ARCH] [--jre] [--exec]
                 [COMMAND] [ARG [ARG ...]]

return a value for $JAVA_HOME

positional arguments:
  COMMAND               COMMAND to execute
  ARG                   Arguments for COMMAND

optional arguments:
  -h, --help            show this help message and exit
  --version VERSION, -v VERSION
                        Filters the returned JVMs by the major platform
                        version in "JVMVersion" form. Example versions:
                        "1.5+", or "1.6*".
  --latest, -l          Filters to the most recent JVM.
  --verbose, -V         Prints the matching list of JVMs and architectures to
                        stderr.
  --architecture ARCH, -a ARCH
                        Filters to the provided architecture. Default is amd64
  --jre, -j             Filters to only matching JREs
  --exec, -e            Executes the command at $JAVA_HOME/bin/<COMMAND> and
                        passes the remaining arguments. Any arguments to
                        select which $JAVA_HOME to use must precede the --exec
                        option.
```
### Examples

Set `$JAVA_HOME` to the JDK 1.8

```bash
export JAVA_HOME=$(java_home --version 1.8)
```

Set `$JAVA_HOME` to the JDK 1.11 and run then `java` command

```bash
java_home --version 1.11 --exec java -version
```

List the available java versions

```bash
java_home --verbose
```

## To Do

* Install script
* Improved handling for "JVMVersion"
* Determining the current architecture is hardcoded because python reports `X86_64` and the JVM is using `amd64`
* Locations of the JVM could vary from `/usr/lib/jvm`
* Default handling return the current JDK directory
* Better support for architectures

## Requirements

* Python 3.x

