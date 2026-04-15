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

#
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

  libmain_validate_bumped_and_git_versions

  defer_ret build_run_ctx_reset_all_persistent

  # cleanup
  build_stage "Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:22.04"
    defer_ret build_run_ctx_reset

    build_run rm -f ./gain_core/gain/__build__.py
    build_run rm -f ./gpf_core/gpf/__build__.py
    build_run rm -f ./gpf_web/gpf_web/__build__.py

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
        gain_core/.coverage* gpf_core/.coverage* gpf_web/.coverage*
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
    build_run rm -f /gpf_version.txt
    build_run bash -c '
        /opt/conda/bin/conda run --no-capture-output -n build \
            invoke -r /release_management current-version > /gpf_version.txt'

    if [ "$gpf_version" == "" ]; then
        version="$(build_run cat /gpf_version.txt)"
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

  # run minio
  build_stage "Run minio"
  {

    local -A ctx_minio

    build_run_ctx_init ctx:ctx_minio "persistent" "container" "minio/minio" \
        "cmd-from-image" "no-def-mounts" \
        'ports:9000' \
        -e MINIO_ROOT_USER=minioadmin \
        -e MINIO_ROOT_PASSWORD=minioadmin \
        --hostname minio --network "${ctx_network["network_id"]}" \
        -- server /data --console-address ":9001"

    defer_ret build_run_ctx_reset ctx:ctx_minio
    build_run_ctx_persist ctx:ctx_minio

    build_run_local echo "Network ID: ${ctx_network["network_id"]}"
    build_run_local sleep 15

    build_run_local docker run \
        --rm --network "${ctx_network["network_id"]}" \
        --entrypoint '/bin/sh'  \
        minio/mc -c '
            /usr/bin/mc alias set local http://minio:9000 minioadmin minioadmin;
            /usr/bin/mc mb local/test-bucket'

}

  # run HTTP server
  build_stage "Run apache"
  {

        local -A ctx_apache

        build_run_ctx_init ctx:ctx_apache "persistent" "container" "httpd:latest" \
           "cmd-from-image" "no-def-mounts" \
           --hostname apache --network "${ctx_network["network_id"]}" \
           -v ./gain_core/tests/.test_grr:/usr/local/apache2/htdocs/

        defer_ret build_run_ctx_reset ctx:ctx_apache
        build_run_ctx_persist ctx:ctx_apache

  }

  build_stage "Diagnostics"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_ctx_reset

    for d in gain_core gpf_core gpf_web; do
      build_run_container bash -c \
        'cd /wd/'"${d}"';
        /opt/conda/bin/conda run --no-capture-output -n gpf \
            python setup.py install'
    done


    # mypy
    build_run_detached bash -c '
      cd /wd/gain_core;
      /opt/conda/bin/conda run --no-capture-output -n gpf mypy gain \
          --exclude gain_core/docs/ \
          --exclude gain_core/docs/conf.py \
          --pretty \
          --show-error-context \
          --no-incremental \
          > /wd/results/mypy_gain_report || true'

    build_run_detached bash -c '
      cd /wd/gpf_core;
      /opt/conda/bin/conda run --no-capture-output -n gpf mypy gpf \
          --exclude gpf_core/docs/ \
          --exclude gpf_core/docs/conf.py \
          --pretty \
          --show-error-context \
          --no-incremental \
          > /wd/results/mypy_gpf_report || true'

    build_run_detached bash -c '
      cd /wd/gpf_web;
      /opt/conda/bin/conda run --no-capture-output -n gpf mypy gpf_web \
          --exclude gpf_web/docs/ \
          --exclude gpf_web/docs/conf.py \
          --exclude gpf_web/conftest.py \
          --pretty \
          --show-error-context \
          --no-incremental \
          > /wd/results/mypy_gpf_web_report || true'

    # ruff
    build_run_detached bash -c '
      cd /wd;
      /opt/conda/bin/conda run --no-capture-output -n gpf \
        ruff check --exclude impala_storage \
        --exclude impala2_storage \
        --exclude typings \
        --exclude migrations \
        --exclude docs \
        --exclude wdae_tests \
        --exclude gpf_web_tests \
        --exclude versioneer.py \
        --exclude _version.py \
        --exclude *.ipynb \
        --exit-zero \
        --output-format=pylint \
        --output-file=/wd/results/ruff_report . || true'

    # pylint
    build_run_detached bash -c '
      cd /wd/;
      gpf_web_files=$(find gpf_web/gpf_web -name "*.py" -not -path "**/migrations/*");
      /opt/conda/bin/conda run --no-capture-output -n gpf \
      pylint gpf_core/gpf gain_core/gain $gpf_web_files -f parseable --reports=no -j 4 \
          --exit-zero > /wd/results/pylint_report || true'
    build_run_container wait

    build_run bash -c '
      cd /wd;
      /opt/conda/bin/conda run --no-capture-output -n gpf python scripts/convert_mypy_output.py \
          results/mypy_gain_report > results/mypy_gain_pylint_report || true'

    build_run bash -c '
      cd /wd;
      /opt/conda/bin/conda run --no-capture-output -n gpf python scripts/convert_mypy_output.py \
          results/mypy_gpf_report > results/mypy_gpf_pylint_report || true'

    build_run bash -c '
      cd /wd;
      /opt/conda/bin/conda run --no-capture-output -n gpf python scripts/convert_mypy_output.py \
          results/mypy_gpf_web_report > results/mypy_gpf_web_pylint_report || true'

    build_run_local cp ./results/mypy_gain_report \
        ./results/mypy_gain_pylint_report \
        ./results/mypy_gpf_report \
        ./results/mypy_gpf_pylint_report \
        ./results/mypy_gpf_web_report \
        ./results/mypy_gpf_web_pylint_report \
        ./results/ruff_report \
        ./results/pylint_report \
        ./test-results/

  }

  build_stage "Tests"
  {
    # run gain_core, gpf_core, gpf_web, demo annotator and vep annotator tests asynchronously
    {
      # gain_core
      {
        local -A ctx_gain
        build_run_ctx_init ctx:ctx_gain "container" "${gpf_dev_image_ref}" \
          --network "${ctx_network["network_id"]}" \
          --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
          --env HTTP_HOST="apache" \
          --env MINIO_HOST="minio" \
          --env AWS_ACCESS_KEY_ID="minioadmin" \
          --env AWS_SECRET_ACCESS_KEY="minioadmin" \
          --env WDAE_EMAIL_HOST="mailhog"

        defer_ret build_run_ctx_reset ctx:ctx_gain

        for d in /wd/gain_core /wd/gpf_core /wd/gpf_web; do
          build_run_container ctx:ctx_gain bash -c \
            '/opt/conda/bin/conda run --no-capture-output -n gpf \
                pip install -e "'"${d}"'"'
        done

        build_run_detached ctx:ctx_gain bash -c '
            cd /wd/gain_core;
            export PYTHONHASHSEED=0;
            /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v \
              --s3 --http \
              -n 10 \
              --durations 20 \
              --cov-config /wd/coveragerc \
              --junitxml=/wd/results/gain-junit.xml \
              --cov gain \
              tests/ || true'
      }

      # gpf_core
      {
        local -A ctx_gpf
        build_run_ctx_init ctx:ctx_gpf "container" "${gpf_dev_image_ref}" \
          --network "${ctx_network["network_id"]}" \
          --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
          --env HTTP_HOST="apache" \
          --env MINIO_HOST="minio" \
          --env AWS_ACCESS_KEY_ID="minioadmin" \
          --env AWS_SECRET_ACCESS_KEY="minioadmin" \
          --env WDAE_EMAIL_HOST="mailhog"

        defer_ret build_run_ctx_reset ctx:ctx_gpf

        for d in /wd/gain_core /wd/gpf_core /wd/gpf_web; do
          build_run_container ctx:ctx_gpf bash -c \
            '/opt/conda/bin/conda run --no-capture-output -n gpf \
                pip install -e "'"${d}"'"'
        done

        build_run_detached ctx:ctx_gpf bash -c '
            cd /wd/gpf_core;
            export PYTHONHASHSEED=0;
            /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v \
              --s3 --http \
              -n 10 \
              --durations 20 \
              --cov-config /wd/coveragerc \
              --junitxml=/wd/results/gpf-junit.xml \
              --cov gpf \
              tests/ || true'
      }

      # gpf_web
      {
        local -A ctx_gpf_web
        build_run_ctx_init ctx:ctx_gpf_web "container" "${gpf_dev_image_ref}" \
          --network "${ctx_network["network_id"]}" \
          --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
          --env HTTP_HOST="apache" \
          --env MINIO_HOST="minio" \
          --env AWS_ACCESS_KEY_ID="minioadmin" \
          --env AWS_SECRET_ACCESS_KEY="minioadmin" \
          --env WDAE_EMAIL_HOST="mailhog"

        defer_ret build_run_ctx_reset ctx:ctx_gpf_web

        for d in /wd/gain_core /wd/gpf_core /wd/gpf_web; do
          build_run_container ctx:ctx_gpf_web bash -c \
            '/opt/conda/bin/conda run --no-capture-output -n gpf \
                pip install -e "'"${d}"'"'
        done

        build_run_detached ctx:ctx_gpf_web bash -c '
            cd /wd/gpf_web;
            export PYTHONHASHSEED=0;
            /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v \
              -n 5 \
              --durations 20 \
              --cov-config /wd/coveragerc \
              --junitxml=/wd/results/gpf-web-junit.xml \
              --cov gpf_web \
              gpf_web || true'
      }
    }

    # wait for the asynchronously ran tests to finish and copy their results
    {
      {
        build_run_container ctx:ctx_gain wait
        build_run_container ctx:ctx_gain cp ./results/gain-junit.xml ./test-results/
      }

      {
        build_run_container ctx:ctx_gpf wait
        build_run_container ctx:ctx_gpf cp ./results/gpf-junit.xml ./test-results/
      }

      {
        build_run_container ctx:ctx_gpf_web wait
        build_run_container ctx:ctx_gpf_web cp ./results/gpf-web-junit.xml ./test-results/
      }

    }

    # create cobertura report for jenkins and coverage html report
    {
      build_run_container ctx:ctx_gpf_web coverage combine \
          gain_core/.coverage gpf_core/.coverage gpf_web/.coverage
      build_run_container ctx:ctx_gpf_web coverage xml
      build_run_container ctx:ctx_gpf_web cp coverage.xml ./test-results/
      build_run_container ctx:ctx_gpf_web coverage html --title GPF -d ./test-results/coverage-html
    }
  }

  build_stage "Package"
  {

    local docker_img_iossifovlab_mamba_base
    docker_img_iossifovlab_mamba_base="$(e docker_img_iossifovlab_mamba_base)"

    build_run_ctx_init "container" "${docker_img_iossifovlab_mamba_base}"
    defer_ret build_run_ctx_reset

    build_run rm -rf gain_core/.coverage* gpf_core/.coverage* gpf_web/.coverage*

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

    build_run cp BUILD gain_core/gain/__build__.py
    build_run cp BUILD gpf_core/gpf/__build__.py
    build_run cp BUILD gpf_web/gpf_web/__build__.py
    build_run cp BUILD impala_storage/impala_storage/__build__.py
    build_run cp BUILD impala2_storage/impala2_storage/__build__.py
    build_run cp BUILD rest_client/rest_client/__build__.py
    build_run cp BUILD federation/federation/__build__.py
    build_run cp BUILD spliceai_annotator/spliceai_annotator/__build__.py

    local image_name="gpf-package"
    build_docker_data_image_create_from_tarball "${image_name}" <(
      build_run_local tar cvf - \
          --exclude __pycache__ \
          --exclude .mypy_cache \
          --exclude .pytest_cache \
          --exclude .coverage \
          --exclude .vscode \
          --exclude .task-log \
          --exclude results \
          --exclude .gitignore \
          --exclude gain_core.egg-info \
          --exclude gpf_core.egg-info \
          --exclude gpf_web.egg-info \
          --exclude gain_core/build \
          --exclude gpf_core/build \
          --exclude gpf_web/build \
          --exclude tests \
          --exclude gpf_web_tests \
          --exclude dask-worker-space \
          --exclude demo-scripts \
          --exclude TESTphastCons100way.bedGraph.gz.tbi \
          --exclude test.txt.gz.tbi \
          --exclude wdae.sql \
          --exclude dist \
          --exclude .DS_Store \
          --exclude conftest.py \
          --exclude pylintrc \
          --transform "s,^,gpf/," \
          gain_core/ gpf_core/ gpf_web/ \
          impala_storage \
          impala2_storage \
          gcp_storage \
          rest_client \
          gain_vep_annotator \
          federation \
          spliceai_annotator \
          environment.yml dev-environment.yml VERSION BUILD
    )
  }

  # post cleanup
  build_stage "Post Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:22.04"
    defer_ret build_run_ctx_reset
    build_run rm -rf ./data/ ./import/ ./downloads ./results
    build_run rm -rf gain_core/gain/__build__.py gpf_core/gpf/__build__.py gpf_web/gpf_web/__build__.py VERSION
    build_run rm -rf impala_storage/impala_storage/__build__.py BUILD
    build_run rm -rf impala2_storage/impala2_storage/__build__.py BUILD
  }

}

main "$@"
