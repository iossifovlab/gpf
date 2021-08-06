#!/bin/bash

set -e

././build.sh preset:"fast" clobber:"allow_if_matching_values" expose_ports:"yes" build_no:"0" stage:"Tests - dae"
././build.sh preset:"fast" clobber:"allow_if_matching_values" expose_ports:"yes" build_no:"0" stage:"Tests - wdae"
