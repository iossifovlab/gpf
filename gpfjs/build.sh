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
    iossifovlab.iossifovlab-containers
  libmain_save_build_env_on_exit
  libbuild_init stage:"$stage" registry.seqpipe.org

  defer_ret build_run_ctx_reset_all_persistent
  defer_ret build_run_ctx_reset

  local node_base_image_ref
  node_base_image_ref="$(e docker_img_iossifovlab_node_base)"
  build_run_ctx_init "container" "$node_base_image_ref"
  defer_ret build_run_ctx_reset

  local gpfjs_version
  if ee_exists "gpfjs_version"; then
      gpfjs_version="$(ee "gpfjs_version")"
  fi

  build_stage "Get gpfjs version"
  {

    build_run git config --global --add safe.directory /wd
    if [ "$gpfjs_version" == "" ]; then
        version="$(build_run invoke -r /release_management current-version)"
        if [ "$version" != "" ]; then
            gpfjs_version=${version}
            ee_set "gpfjs_version" "$gpfjs_version"
            build_run echo "{\"version\": \"${version}\"}" > "version.json"
        fi
    fi

    build_run echo "$(ee 'gpfjs_version')"
  }

  build_stage "Clean and fetch fresh dependencies"
  {
    build_run rm -rf dist dist.orig
    build_run rm -rf node_modules package-lock.json
    build_run npm install
  }

  build_stage "Lint"
  {
    build_run bash -c './node_modules/eslint/bin/eslint.js "**/*.{html,ts}" --format checkstyle >ts-lint-report.xml || echo "eslint exited with $?"'
    build_run bash -c './node_modules/.bin/stylelint --custom-formatter ./node_modules/stylelint-checkstyle-formatter "**/*.css" >css-lint-report.xml \
      || echo "stylelint exited with $?"'
  }

  build_stage "Tests"
  {
    build_run bash -c 'npm run-script test:ci || false'
  }

  build_stage "Compile production"
  {
    build_run rm -rf dist/
  
    build_run npm run-script ng build -- --aot --configuration 'production' --base-href '/gpf_prefix/' --deploy-url '/gpf_prefix/'
    build_run /usr/bin/python3 ppindex.py
  }

  build_stage "Package and clean production"
  {
    local gpfjs_version="$(ee 'gpfjs_version')"
    local gpfjs_tag=$(e gpfjs_tag)
    build_run echo $gpfjs_tag
    local __gpfjs_build_no=$(e __gpfjs_build_no)
    build_run echo $__gpfjs_build_no

    build_run_container bash -c '
      echo "'"${gpfjs_version}"'" > dist/gpfjs/VERSION.txt
    '
    build_run_container bash -c '
      echo "'"${gpfjs_tag}"'-'"${__gpfjs_build_no}"'" >> dist/gpfjs/BUILD.txt
    '

    local -A ctx_sentry_cli
    build_run_ctx_init ctx:ctx_sentry_cli "local"
    defer_ret build_run_ctx_reset ctx:ctx_sentry_cli
    build_run ctx:ctx_sentry_cli docker run --rm -v "$PWD":/work getsentry/sentry-cli sourcemaps inject ./dist

    local image_name="gpfjs-production-package"
    build_docker_data_image_create_from_tarball "${image_name}" <(
        build_run_local tar cvf - \
            -C dist \
            gpfjs/
      )

  }

  build_stage "Compile conda package"
  {
    build_run rm -rf dist/
  
    build_run npm run-script ng build -- --aot --configuration 'conda' --base-href '/gpfjs/' --deploy-url '/static/gpfjs/gpfjs/'
    build_run /usr/bin/python3 ppindex.py
  }

  build_stage "Package a clean conda build"
  {
    local gpfjs_version="$(ee 'gpfjs_version')"
    local gpfjs_tag=$(e gpfjs_tag)
    build_run echo $gpfjs_tag
    local __gpfjs_build_no=$(e __gpfjs_build_no)
    build_run echo $__gpfjs_build_no

    build_run_container bash -c '
      echo "'"${gpfjs_version}"'" > dist/gpfjs/VERSION.txt
    '
    build_run_container bash -c '
      echo "'"${gpfjs_tag}"'-'"${__gpfjs_build_no}"'" >> dist/gpfjs/BUILD.txt
    '
  
    local image_name="gpfjs-gpfjs-package"
    build_docker_data_image_create_from_tarball "${image_name}" <(
        build_run_local tar cvf - \
            -C dist \
            gpfjs/
      )
  
    local image_name="gpfjs-conda-package"
    build_docker_data_image_create_from_tarball "${image_name}" <(
        build_run_local tar cvf - \
            -C dist \
            gpfjs/
      )

  }

}

main "$@"
