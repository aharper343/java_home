#!/bin/bash -e

if [ $(id --user) -ne 0 ] ; then
  echo "${0}: should be via sudo"
  exit 1
fi
install_path="/usr/libexec"
install_name="java_home"
install_to="${install_path}/${install_name}"
set -x
cp src/java_home.py "${install_to}"
chmod +x,-w "${install_to}"
chown root:root "${install_to}"