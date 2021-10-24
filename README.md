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

`java_home` - return a value for `$JAVA_HOME`

* `-h` or `--help` : This message
* `-v` or `--version`  `VERSION`
    Filters the returned JVMs by the major platform version in "JVMVersion" form.
    Example versions: "1.5+", or "1.6*".
* `-V` or `--verbose`
    Prints the matching list of JVMs and architectures to stderr.
* `-e` or `--exec` `COMMAND [ARG ..]`
    Executes the command at `$JAVA_HOME/bin/<command>` and passes the remaining arguments.
    Any arguments to select which `$JAVA_HOME` to use must precede the `--exec` option.
* `-j` or `--jre`
    Filters to only matching JREs
* `-l` or `--latest`
    Filters to the most recent JVM.

**NOTE**:
* `-v` or `--version` `VERSION` and `-l` `--latest` cannot be used at the same tine
* `-e` or `--exec` `COMMAND [ARG ...]` must be used with either
    `-v` or `--version` `VERSION`
    `-l` or `--latest`

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

## Requirements

* Python 3.x

