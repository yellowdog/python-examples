#!/bin/bash

# Simple test script to be executed by a YellowDog Worker

set -e

echo
uname -a
echo

echo "Environment:"
echo
set
echo
echo "Additional Arguments:" $@
echo
echo "Working Directory:" $PWD
echo
if command -v tree &> /dev/null
then
  echo "Tree output:"
  echo
  tree
  echo
fi
echo "Script Directory:" $(dirname $(readlink -f $0))
sleep 3
echo
echo "Slept 3s ... done"
