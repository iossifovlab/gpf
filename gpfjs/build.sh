#!/bin/bash

shopt -s extdebug
shopt -s inherit_errexit
set -e

. build-scripts/loader-extended.bash

loader_addpath build-scripts/

# shellcheck source=build-scripts/libmain.sh
include libmain.sh
# shellcheck source=build-scripts/libbuild.sh
include libbuild.sh
# shellcheck source=build-scripts/libdefer.sh
include libdefer.sh

function main() {
  libmain_init
  libmain_init_build_env seqpipe-containers
  libmain_save_build_env_on_exit gpfjs

  libbuild_init gpfjs

  local image_ref
  image_ref="$(e docker_img_seqpipe_node_base)"


  local stage="$1"
  build_run_init "container" "$image_ref" "$stage"

  defer_ret build_run_reset ctx

  build_stage "Clean and fetch fresh dependencies"
  build_run echo rm -rf node_modules package-lock.json
  build_run echo npm install
  build_stage "Lint"
  build_run echo ng lint --format checkstyle > ts-lint-report.xml || echo "tslint exited with $?"
  build_run echo sed -i '$ d' ts-lint-report.xml
  build_stage "Tests"
  build_run echo ng test -- --no-watch --no-progress --code-coverage --browsers=ChromeHeadlessCI || true
  build_stage "Clean and package"
  build_run echo rm -rf dist/
	build_run echo ng build --prod --aot --configuration 'default' --base-href '/gpf_prefix/' --deploy-url '/gpf_prefix/'
	build_stage "ppindex"
	build_run echo ppindex.py

}

main "$@"
