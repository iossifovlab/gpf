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

  build_stage "Clean and fetch fresh dependencies"
  {
    build_run rm -rf dist
    build_run rm -rf node_modules package-lock.json
    build_run apt-get remove -y nodejs
    build_run bash -c 'curl -sL https://deb.nodesource.com/setup_14.x  | bash -'
    build_run apt-get install -y nodejs
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

  build_stage "Sonarqube Analysis"
  {
    local gpfjs_git_branch=$(e gpfjs_git_branch)

    build_run_local echo "gpfjs_git_branch=$gpfjs_git_branch"
    build_run_local echo "SONARQUBE_DEFAULT_TOKEN=$SONARQUBE_DEFAULT_TOKEN"

    if [ "$SONARQUBE_DEFAULT_TOKEN" != "" ] && [ "$gpfjs_git_branch" = "master" ]; then

      build_run_local echo "Sonarqube stage started"

      build_run_local docker run --rm \
          -e SONAR_HOST_URL="http://sonarqube.seqpipe.org:9000" \
          -e SONAR_LOGIN="${SONARQUBE_DEFAULT_TOKEN}" \
          -v "$(pwd):/usr/src" \
          sonarsource/sonar-scanner-cli \
          -Dsonar.projectKey=gpfjs \
          -Dsonar.python.version=3.9 \
          -Dsonar.javascript.lcov.reportPaths=coverage/lcov.info

    else
      build_run_local echo "Sonarqube stage skipped"
    fi
  }

  build_stage "Compile production"
  {
    build_run rm -rf dist/
  
    build_run npm run-script ng build -- --aot --configuration 'production' --base-href '/gpf_prefix/' --deploy-url '/gpf_prefix/'
    build_run python ppindex.py
  }

  build_stage "Package and clean production"
  {
    local gpfjs_tag=$(e gpfjs_tag)
    build_run echo $gpfjs_tag
    local __gpfjs_build_no=$(e __gpfjs_build_no)
    build_run echo $__gpfjs_build_no

    build_run_container bash -c '
      echo "'"${gpfjs_tag}"'" > dist/gpfjs/VERSION.txt
    '
    build_run_container bash -c '
      echo "'"${gpfjs_tag}"'-'"${__gpfjs_build_no}"'" >> dist/gpfjs/VERSION.txt
    '
  
    local image_name="gpfjs-package"
    build_docker_data_image_create_from_tarball "${image_name}" <(
        build_run_local tar cvf - \
            -C dist \
            gpfjs/
      )

  }

  build_stage "Compile conda package"
  {
    build_run rm -rf dist/
  
    build_run npm run-script ng build -- --aot --configuration 'conda' --base-href '' --deploy-url '/static/gpfjs/'
    build_run python ppindex.py
  }

  build_stage "Package and clean conda"
  {
    local gpfjs_tag=$(e gpfjs_tag)
    build_run echo $gpfjs_tag
    local __gpfjs_build_no=$(e __gpfjs_build_no)
    build_run echo $__gpfjs_build_no

    build_run_container bash -c '
      echo "'"${gpfjs_tag}"'" > dist/gpfjs/VERSION.txt
    '
    build_run_container bash -c '
      echo "'"${gpfjs_tag}"'-'"${__gpfjs_build_no}"'" >> dist/gpfjs/VERSION.txt
    '
  
    local image_name="gpfjs-conda-package"
    build_docker_data_image_create_from_tarball "${image_name}" <(
        build_run_local tar cvf - \
            -C dist \
            gpfjs/
      )

  }

}

main "$@"
