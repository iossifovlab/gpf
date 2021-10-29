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
# shellcheck source=build-scripts/libopt.sh
include libopt.sh

function main() {
  local -A options
  libopt_parse options \
    stage:all preset:fast clobber:allow_if_matching_values build_no:0 generate_jenkins_init:no expose_ports:no -- "$@"

  local preset="${options["preset"]}"
  local stage="${options["stage"]}"
  local clobber="${options["clobber"]}"
  local build_no="${options["build_no"]}"
  local generate_jenkins_init="${options["generate_jenkins_init"]}"
  local expose_ports="${options["expose_ports"]}"

  libmain_init iossifovlab.gpfjs gpfjs
  libmain_init_build_env \
    clobber:"$clobber" preset:"$preset" build_no:"$build_no" generate_jenkins_init:"$generate_jenkins_init" expose_ports:"$expose_ports" \
    seqpipe.seqpipe-containers
  libmain_save_build_env_on_exit
  libbuild_init stage:"$stage" registry.seqpipe.org

  defer_ret build_run_ctx_reset_all_persistent
  defer_ret build_run_ctx_reset

  local node_base_image_ref
  node_base_image_ref="$(e docker_img_seqpipe_node_base)"
  build_run_ctx_init "container" "$node_base_image_ref"
  defer_ret build_run_ctx_reset

  build_stage "Clean and fetch fresh dependencies"
  {
    build_run rm -rf node_modules package-lock.json
    build_run npm install
  }

  build_stage "Lint"
  {
    build_run ng lint --format checkstyle >ts-lint-report.xml || echo "eslint exited with $?"
    build_run sed -i '1,2d' ts-lint-report.xml
    build_run ./node_modules/.bin/stylelint --custom-formatter ./node_modules/stylelint-checkstyle-formatter "**/*.css" >css-lint-report.xml \
      || echo "stylelint exited with $?"
  }

  build_stage "Tests"
  {
    build_run ng test -- --no-watch --no-progress --code-coverage --browsers=ChromeHeadlessCI || true
  }

  build_stage "Clean and package"
  {
    build_run rm -rf dist/
    build_run ng build --prod --aot --configuration 'default' --base-href '/gpf_prefix/' --deploy-url '/gpf_prefix/'
  }

}

main "$@"
