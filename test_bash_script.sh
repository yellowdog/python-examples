#!/bin/bash

################################################################################
# Clean up child processes on Task Abort

# Simple cleanup function that kills immediate child processes only
kill_child_procs() {
  local PIDS
  PIDS=$(jobs -p)
  if [ -n "$PIDS" ]
  then
    echo "Aborted: killing child processes [$PIDS]"
    kill $PIDS &>/dev/null
  fi
}

# Recursive cleanup function that kills all descendent processes
kill_descendent_procs() {
    local PID="$1"
    local INCLUDE_SELF="${2:-false}"
    if CHILDREN="$(pgrep -P "$PID")"; then
        for CHILD in $CHILDREN; do
            kill_descendent_procs "$CHILD" true
        done
    fi
    if [[ "$INCLUDE_SELF" == true ]]; then
        kill "$PID" &>/dev/null
    fi
}

# Trap EXIT and clean up
#trap "kill_descendent_procs $$" EXIT
trap kill_child_procs EXIT
################################################################################

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
sleep 1m
echo
echo "Slept 1m ... done"
exit 1
