#!/bin/bash

set -e

./build.sh preset:"fast" clobber:"allow" expose_ports:"yes" build_no:"0" stage:"Post Cleanup"
