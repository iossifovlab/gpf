#!/bin/bash

set -e

./build.sh preset:"fast" expose_ports:"yes" stage:"Jenkinsfile.generated-stages.all"
./build.sh preset:"fast" clobber:"allow" expose_ports:"yes" build_no:"0" stage:"Cleanup"
./build.sh preset:"fast" clobber:"allow" expose_ports:"yes" build_no:"0" stage:"Create gpf-dev docker image"
./build.sh preset:"fast" clobber:"allow" expose_ports:"yes" build_no:"0" stage:"Prepare GPF data"
./build.sh preset:"fast" clobber:"allow" expose_ports:"yes" build_no:"0" stage:"Prepare GPF remote data"
./build.sh preset:"fast" clobber:"allow" expose_ports:"yes" build_no:"0" stage:"Run cluster"
./build.sh preset:"fast" clobber:"allow" expose_ports:"yes" build_no:"0" stage:"Import test data to impala"
