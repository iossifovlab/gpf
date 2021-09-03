#!/bin/bash

shopt -s extdebug
shopt -s inherit_errexit
set -e

. build-scripts/loader-extended.bash

loader_addpath build-scripts/

# shellcheck source=build-scripts/libopt.sh
include libopt.sh

declare -A options
libopt_parse options \
  stage:all preset:fast clobber:allow_if_matching_values build_no:0 generate_jenkins_init:no expose_ports:yes -- "$@"

preset="${options["preset"]}"
stage="${options["stage"]}"
clobber="${options["clobber"]}"
build_no="${options["build_no"]}"
generate_jenkins_init="${options["generate_jenkins_init"]}"
expose_ports="${options["expose_ports"]}"

./build.sh preset:"$preset" clobber:"$clobber" expose_ports:"$expose_ports" stage:"Post Cleanup"
