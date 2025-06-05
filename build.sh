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
# shellcheck source=build-scripts/liblog.sh
include liblog.sh
# shellcheck source=build-scripts/libopt.sh
include libopt.sh

function main() {
  local -A options
  libopt_parse options \
    stage:all preset:slow clobber:allow_if_matching_values build_no:0 \
    generate_jenkins_init:no expose_ports:no -- "$@"

  local preset="${options["preset"]}"
  local stage="${options["stage"]}"
  local clobber="${options["clobber"]}"
  local build_no="${options["build_no"]}"
  local generate_jenkins_init="${options["generate_jenkins_init"]}"
  local expose_ports="${options["expose_ports"]}"

  libmain_init iossifovlab.gpf gpf
  libmain_init_build_env \
    clobber:"$clobber" preset:"$preset" build_no:"$build_no" \
    generate_jenkins_init:"$generate_jenkins_init" expose_ports:"$expose_ports" \
    iossifovlab.iossifovlab-containers

  libmain_save_build_env_on_exit
  libbuild_init stage:"$stage" registry.seqpipe.org

  liblog_verbosity=6

  libmain_validate_bumped_and_git_versions

  defer_ret build_run_ctx_reset_all_persistent

  # cleanup
  build_stage "Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:22.04"
    defer_ret build_run_ctx_reset

    build_run rm -f ./dae/dae/__build__.py
    build_run rm -f ./wdae/wdae/__build__.py

    build_run rm -rf ./data/ ./import/ ./downloads ./results
    build_run_local mkdir -p ./data/ ./import/ ./downloads ./results ./cache

    build_run rm -rf ./test-results/
    build_run_local mkdir -p ./test-results/

    build_run rm -rf \
      ./integration/remote/data/studies \
      ./integration/remote/data/pheno \
      ./integration/remote/data/wdae

    build_run rm -rf \
      ./integration/local/data/studies \
      ./integration/local/data/pheno \
      ./integration/local/data/wdae

    build_run rm -rf \
        dae/.coverage*
  }

  local gpf_version
  if ee_exists "gpf_version"; then
      gpf_version="$(ee "gpf_version")"
  fi

  build_stage "Get GPF version"
  {
    local docker_img_iossifovlab_mamba_base
    docker_img_iossifovlab_mamba_base="$(e docker_img_iossifovlab_mamba_base)"

    build_run_ctx_init "container" "${docker_img_iossifovlab_mamba_base}"
    defer_ret build_run_ctx_reset

    build_run git config --global --add safe.directory /wd
    if [ "$gpf_version" == "" ]; then
        version="$(build_run invoke -r /release_management current-version)"
        # version="$(build_run git describe)"
        if [ "$version" != "" ]; then
            gpf_version=${version}
            ee_set "gpf_version" "$gpf_version"
        fi
    fi

    build_run echo "${gpf_version}"

  }


  local gpf_dev_image="gpf-dev"
  local gpf_dev_image_ref
  # create gpf docker image
  build_stage "Create gpf-dev docker image"
  {
    local docker_img_iossifovlab_mamba_base_tag
    docker_img_iossifovlab_mamba_base_tag="$(e docker_img_iossifovlab_mamba_base_tag)"
    build_docker_image_create "$gpf_dev_image" . ./Dockerfile.seqpipe "$docker_img_iossifovlab_mamba_base_tag"
    gpf_dev_image_ref="$(e docker_img_gpf_dev)"
  }

  build_stage "Prepare GRR config"
  {
    build_run_local bash -c "mkdir -p ./cache"
    build_run_local bash -c "touch ./cache/grr_definition.yaml"
    build_run_local bash -c 'cat > ./cache/grr_definition.yaml << EOT
id: "default"
type: "url"
url: "https://grr.seqpipe.org/"
cache_dir: "/wd/cache/grrCache"
EOT
'

  }

  build_stage "Create network"
  {
    # create network
    local -A ctx_network
    build_run_ctx_init ctx:ctx_network "persistent" "network"
    build_run_ctx_persist ctx:ctx_network
  }

  # run localstack
  build_stage "Run localstack"
  {

        local -A ctx_localstack

        build_run_ctx_init ctx:ctx_localstack "persistent" "container" "localstack/localstack" \
           "cmd-from-image" "no-def-mounts" \
           'ports:4566,4510-4559' \
           --hostname localstack --network "${ctx_network["network_id"]}" --workdir /opt/code/localstack/

        defer_ret build_run_ctx_reset ctx:ctx_localstack
        build_run_ctx_persist ctx:ctx_localstack

  }

  # run HTTP server
  build_stage "Run apache"
  {

        local -A ctx_apache

        build_run_ctx_init ctx:ctx_apache "persistent" "container" "httpd:latest" \
           "cmd-from-image" "no-def-mounts" \
           --hostname apache --network "${ctx_network["network_id"]}" \
           -v ./dae/tests/.test_grr:/usr/local/apache2/htdocs/

        defer_ret build_run_ctx_reset ctx:ctx_apache
        build_run_ctx_persist ctx:ctx_apache

  }

  build_stage "Diagnostics"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_ctx_reset

    for d in dae wdae impala_storage impala2_storage gcp_storage external_demo_annotator external_vep_annotator; do
      build_run_container bash -c \
        'cd /wd;
        /opt/conda/bin/conda run --no-capture-output -n gpf \
            pip install -e "'"${d}"'"'
    done

    # ruff
    build_run_detached bash -c '
      cd /wd;
      /opt/conda/bin/conda run --no-capture-output -n gpf ruff check \
        --exit-zero \
        --output-format=pylint \
        --output-file=/wd/results/ruff_report . || true'

    # pylint
    build_run_detached bash -c '
      cd /wd/;
      wdae_files=$(find wdae/wdae -name "*.py" -not -path "**/migrations/*");
      /opt/conda/bin/conda run --no-capture-output -n gpf
      pylint dae/dae impala_storage/impala_storage  $wdae_files -f parseable --reports=no -j 4 \
          --exit-zero > /wd/results/pylint_report || true'

    # pyright
    build_run_detached bash -c '
      cd /wd;
      /opt/conda/bin/conda run --no-capture-output -n gpf \
          pyright dae wdae impala_storage impala2_storage gcp_storage external_demo_annotator external_vep_annotator \
          --outputjson \
          > /wd/results/pyright_report_raw.json || true'

    build_run_container wait

    build_run bash -c '
      cd /wd;
      /opt/conda/bin/conda run --no-capture-output -n gpf python scripts/convert_pyright_output.py \
          results/pyright_report_raw.json > results/pyright_report || true'

    build_run_local cp ./results/pyright_report \
      ./results/ruff_report \
      ./results/pylint_report \
      ./test-results/
  }

  build_stage "Tests"
  {
    # run dae, wdae, dae integration, demo annotator and vep annotator tests asynchronously
    {
      # dae
      {
        local -A ctx_dae
        build_run_ctx_init ctx:ctx_dae "container" "${gpf_dev_image_ref}" \
          --network "${ctx_network["network_id"]}" \
          --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
          --env HTTP_HOST="apache" \
          --env LOCALSTACK_HOST="localstack" \
          --env AWS_ACCESS_KEY_ID="foo" \
          --env AWS_SECRET_ACCESS_KEY="foo" \
          --env WDAE_EMAIL_HOST="mailhog"

        defer_ret build_run_ctx_reset ctx:ctx_dae

        for d in /wd/dae /wd/wdae; do
          build_run_container ctx:ctx_dae bash -c \
            '/opt/conda/bin/conda run --no-capture-output -n gpf \
                pip install -e "'"${d}"'"'
        done

        build_run_detached ctx:ctx_dae bash -c '
            cd /wd/dae;
            export PYTHONHASHSEED=0;
            /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v \
              --s3 --http \
              -n 10 \
              --durations 20 \
              --cov-config /wd/coveragerc \
              --junitxml=/wd/results/dae-junit.xml \
              --cov dae \
              tests/ || true'
      }

      # wdae
      {
        local -A ctx_wdae
        build_run_ctx_init ctx:ctx_wdae "container" "${gpf_dev_image_ref}" \
          --network "${ctx_network["network_id"]}" \
          --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
          --env HTTP_HOST="apache" \
          --env LOCALSTACK_HOST="localstack" \
          --env WDAE_EMAIL_HOST="mailhog"

        defer_ret build_run_ctx_reset ctx:ctx_wdae

        for d in /wd/dae /wd/wdae; do
          build_run_container ctx:ctx_wdae bash -c \
            '/opt/conda/bin/conda run --no-capture-output -n gpf \
                pip install -e "'"${d}"'"'
        done

        build_run_detached ctx:ctx_wdae bash -c '
            cd /wd/wdae;
            export PYTHONHASHSEED=0;
            /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v \
              -n 5 \
              --durations 20 \
              --cov-config /wd/coveragerc \
              --junitxml=/wd/results/wdae-junit.xml \
              --cov wdae \
              wdae || true'
      }

      # demo_annotator
      {
        local -A ctx_demo
        build_run_ctx_init ctx:ctx_demo "container" "${gpf_dev_image_ref}" \
          --network "${ctx_network["network_id"]}" \
          --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
          --env HTTP_HOST="apache" \
          --env LOCALSTACK_HOST="localstack" \
          --env AWS_ACCESS_KEY_ID="foo" \
          --env AWS_SECRET_ACCESS_KEY="foo" \
          --env WDAE_EMAIL_HOST="mailhog"

        defer_ret build_run_ctx_reset ctx:ctx_demo

        for d in /wd/dae /wd/wdae /wd/external_demo_annotator; do
          build_run_container ctx:ctx_demo bash -c \
            '/opt/conda/bin/conda run --no-capture-output -n gpf \
                pip install -e "'"${d}"'"'
        done

        build_run_detached ctx:ctx_demo bash -c '
            cd /wd/external_demo_annotator;
            export PYTHONHASHSEED=0;
            /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v \
              -n 5 \
              --durations 20 \
              --cov-config /wd/coveragerc \
              --junitxml=/wd/results/demo-annotator-junit.xml \
              --cov demo_annotator \
              demo_annotator/ || true'
      }
      # vep_annotator
      {
        local -A ctx_vep
        build_run_ctx_init ctx:ctx_vep "container" "${gpf_dev_image_ref}" \
          --network "${ctx_network["network_id"]}" \
          --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
          --env HTTP_HOST="apache" \
          --env LOCALSTACK_HOST="localstack" \
          --env AWS_ACCESS_KEY_ID="foo" \
          --env AWS_SECRET_ACCESS_KEY="foo" \
          --env WDAE_EMAIL_HOST="mailhog"

        defer_ret build_run_ctx_reset ctx:ctx_vep

        for d in /wd/dae /wd/wdae /wd/external_vep_annotator; do
          build_run_container ctx:ctx_vep bash -c \
            '/opt/conda/bin/conda run --no-capture-output -n gpf \
                pip install -e "'"${d}"'"'
        done

        build_run_detached ctx:ctx_vep bash -c '
            cd /wd/external_vep_annotator;
            export PYTHONHASHSEED=0;
            /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v \
              -n 5 \
              --durations 20 \
              --cov-config /wd/coveragerc \
              --junitxml=/wd/results/vep-annotator-junit.xml \
              --cov vep_annotator \
              vep_annotator/ || true'
      }
    }

    # wait for the asynchronously ran tests to finish and copy their results
    {
      {
        build_run_container ctx:ctx_dae wait
        build_run_container ctx:ctx_dae cp ./results/dae-junit.xml ./test-results/
      }

      {
        build_run_container ctx:ctx_wdae wait
        build_run_container ctx:ctx_wdae cp ./results/wdae-junit.xml ./test-results/
      }

      {
        build_run_container ctx:ctx_demo wait
        build_run_container ctx:ctx_demo cp ./results/demo-annotator-junit.xml ./test-results/
      }

      {
        build_run_container ctx:ctx_vep wait
        build_run_container ctx:ctx_vep cp ./results/vep-annotator-junit.xml ./test-results/
      }
    }

    # create cobertura report for jenkins and coverage html report for dae, wdae, dae_integ, wdae_integ
    {
      # the commands are run in the ctx_wdae_integ context to not rely on host to have the 'coverage' commandline tool
      build_run_container ctx:ctx_wdae coverage combine dae/.coverage wdae/.coverage
      build_run_container ctx:ctx_wdae coverage xml
      build_run_container ctx:ctx_wdae cp coverage.xml ./test-results/
      build_run_container ctx:ctx_wdae coverage html --title GPF -d ./test-results/coverage-html
    }
  }

  build_stage "Package"
  {

    local docker_img_iossifovlab_mamba_base
    docker_img_iossifovlab_mamba_base="$(e docker_img_iossifovlab_mamba_base)"

    build_run_ctx_init "container" "${docker_img_iossifovlab_mamba_base}"
    defer_ret build_run_ctx_reset

    build_run rm -rf dae/.coverage*

    local gpf_tag=$(e gpf_tag)
    local __gpf_build_no=$(e __gpf_build_no)

    local gpf_git_branch=$(e gpf_git_branch)
    local gpf_git_describe=$(e gpf_git_describe)

    build_run bash -c '
      echo '"${gpf_version}"' > VERSION
      echo "" >> VERSION
    '

    build_run bash -c '
      echo "# pylint: skip-file" > BUILD
      echo "# type: ignore" >> BUILD
      echo "# ruff: noqa" >> BUILD
      echo "VERSION = \"'"${gpf_version}"'\"" >> BUILD
      echo "GIT_DESCRIBE = \"'"${gpf_git_describe}"'\"" >> BUILD
      echo "GIT_BRANCH = \"'"${gpf_git_branch}"'\"" >> BUILD
      echo "BUILD = \"'"${gpf_tag}"'-'"${__gpf_build_no}"'\"" >> BUILD
      echo "" >> BUILD
    '

    build_run cp BUILD dae/dae/__build__.py
    build_run cp BUILD wdae/wdae/wdae/__build__.py
    build_run cp BUILD impala_storage/impala_storage/__build__.py
    build_run cp BUILD impala2_storage/impala2_storage/__build__.py
    build_run cp BUILD rest_client/rest_client/__build__.py

    local image_name="gpf-package"
    build_docker_data_image_create_from_tarball "${image_name}" <(
      build_run_local tar cvf - \
          --exclude __pycache__ \
          --exclude .mypy_cache \
          --exclude .pytest_cache \
          --exclude .coverage \
          --exclude .vscode \
          --exclude results \
          --exclude .gitignore \
          --exclude gpf_dae.egg-info \
          --exclude dae/tmp \
          --exclude dae/build \
          --exclude wdae/build \
          --exclude tests \
          --exclude wdae_tests \
          --exclude dask-worker-space \
          --exclude demo-scripts \
          --exclude TESTphastCons100way.bedGraph.gz.tbi \
          --exclude test.txt.gz.tbi \
          --exclude wdae.sql \
          --exclude dist \
          --exclude .DS_Store \
          --exclude conftest.py \
          --exclude gpf_wdae.egg-info \
          --exclude pyrightconfig.json \
          --exclude pylintrc \
          --transform "s,^,gpf/," \
          dae/ wdae/ \
          impala_storage \
          impala2_storage \
          gcp_storage \
          rest_client \
          external_vep_annotator \
          federation \
          environment.yml dev-environment.yml VERSION BUILD
    )
  }

  # post cleanup
  build_stage "Post Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:22.04"
    defer_ret build_run_ctx_reset
    build_run rm -rf ./data/ ./import/ ./downloads ./results
    build_run rm -rf dae/dae/__build__.py wdae/wdae/__build__.py VERSION
    build_run rm -rf impala_storage/impala_storage/__build__.py BUILD
    build_run rm -rf impala2_storage/impala2_storage/__build__.py BUILD
  }

}

main "$@"
