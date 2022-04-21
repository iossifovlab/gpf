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
    stage:all preset:fast clobber:allow_if_matching_values build_no:0 \
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
    iossifovlab.data-hg19-startup iossifovlab.iossifovlab-containers

  libmain_save_build_env_on_exit
  libbuild_init stage:"$stage" registry.seqpipe.org

  liblog_verbosity=6

  libmain_validate_bumped_and_git_versions

  defer_ret build_run_ctx_reset_all_persistent

  # cleanup
  build_stage "Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:20.04"
    defer_ret build_run_ctx_reset

    build_run rm -rvf ./data/ ./import/ ./downloads ./results
    build_run_local mkdir -p ./data/ ./import/ ./downloads ./results ./cache

    build_run rm -rvf ./test-results/
    build_run_local mkdir -p ./test-results/

  }

  local gpf_dev_image="gpf-dev"
  local gpf_dev_image_ref
  # create gpf docker image
  build_stage "Create gpf-dev docker image"
  {
    local docker_img_iossifovlab_anaconda_base_tag
    docker_img_iossifovlab_anaconda_base_tag="$(e docker_img_iossifovlab_anaconda_base_tag)"
    build_docker_image_create "$gpf_dev_image" . ./Dockerfile "$docker_img_iossifovlab_anaconda_base_tag"
    gpf_dev_image_ref="$(e docker_img_gpf_dev)"
  }

  # run impala
  build_stage "Run impala"
  {
    # create network
    {
      local -A ctx_network
      build_run_ctx_init ctx:ctx_network "persistent" "network"
      build_run_ctx_persist ctx:ctx_network
    }
    # setup impala
    {
      local -A ctx_impala
      build_run_ctx_init ctx:ctx_impala "persistent" "container" "seqpipe/seqpipe-docker-impala:latest" \
          "cmd-from-image" "no-def-mounts" \
          ports:21050,8020,25000,25010,25020 --hostname impala --network "${ctx_network["network_id"]}"

      defer_ret build_run_ctx_reset ctx:ctx_impala

      build_run_container ctx:ctx_impala /wait-for-it.sh -h localhost -p 21050 -t 300

      build_run_ctx_persist ctx:ctx_impala
    }
  }

  # prepare gpf data
  build_stage "Prepare GPF data"
  {
    build_run_ctx_init "local"
    defer_ret build_run_ctx_reset

    # find image
    local data_hg19_startup_image_ref
    data_hg19_startup_image_ref="$(e docker_data_img_data_hg19_startup)"

    # copy data
    build_run_local mkdir -p ./data/data-hg19-startup
    build_docker_image_cp_from "$data_hg19_startup_image_ref" ./data/data-hg19-startup /

    # reset instance conf
    build_run_local bash -c 'sed -i \
      -e s/"^      - localhost.*$/      - impala"/g \
      -e s/"^      host: localhost.*$/      host: impala"/g \
      ./data/data-hg19-startup/gpf_instance.yaml
    '

    build_run_local bash -c "mkdir -p ./cache"
    build_run_local bash -c "touch ./cache/grr_definition.yaml"
    build_run_local bash -c 'cat > ./cache/grr_definition.yaml << EOT
id: "default"
type: "url"
url: "https://grr.seqpipe.org/"
cache_dir: "/wd/cache/grrCache"
EOT
'
    build_run_ctx_init "container" "ubuntu:20.04"
    defer_ret build_run_ctx_reset

    # cleanup
    build_run_container rm -rvf \
      ./data/data-hg19-startup/studies/* \
      ./data/data-hg19-startup/pheno/* \
      ./data/data-hg19-startup/wdae/wdae.sql

    build_run_ctx_init "local"
    defer_ret build_run_ctx_reset

    # setup directory structure
    build_run_local mkdir -p \
      ./data/data-hg19-startup/genomic-scores-hg19 \
      ./data/data-hg19-startup/genomic-scores-hg38 \
      ./data/data-hg19-startup/wdae
  }

  build_stage "Prepare GPF remote"
  {
    # prepare raw data
    {
      build_run_ctx_init "local"
      defer_ret build_run_ctx_reset

      # find image
      local data_hg19_startup_image_ref
      data_hg19_startup_image_ref="$(e docker_data_img_data_hg19_startup)"

      # copy data
      build_run_local mkdir -p ./data/data-hg19-remote
      build_docker_image_cp_from "$data_hg19_startup_image_ref" ./data/data-hg19-remote /

      # reset instance conf
    # reset instance conf
    build_run_local bash -c 'sed -i \
      -e s/"^      - localhost.*$/      - impala"/g \
      -e s/"^      host: localhost.*$/      host: impala"/g \
      ./data/data-hg19-remote/gpf_instance.yaml
      '

      build_run_ctx_init "container" "ubuntu:20.04"
      defer_ret build_run_ctx_reset

      # cleanup
      build_run_container rm -rvf \
        ./data/data-hg19-remote/studies/* \
        ./data/data-hg19-remote/pheno/* \
        ./data/data-hg19-remote/wdae/wdae.sql

      build_run_ctx_init "local"
      defer_ret build_run_ctx_reset

      # setup directory structure
      build_run_local mkdir -p \
        ./data/data-hg19-remote/genomic-scores-hg19 \
        ./data/data-hg19-remote/genomic-scores-hg38 \
        ./data/data-hg19-remote/wdae

      # prepare phenotype data
      {
        local docker_data_img_phenotype_comp_data
        docker_data_img_phenotype_comp_data="$(e docker_data_img_phenotype_comp_data)"

        # copy data
        build_docker_image_cp_from "$docker_data_img_phenotype_comp_data" ./import /
      }
    }
  }

  build_stage "Import GPF remote data"
  {

    local -A ctx_gpf_remote
    build_run_ctx_init ctx:ctx_gpf_remote "persistent" "container" "${gpf_dev_image_ref}" \
      ports:21010 \
      --hostname gpfremote \
      --network "${ctx_network["network_id"]}" \
      --env DAE_DB_DIR="/wd/data/data-hg19-remote/" \
      --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" 
    defer_ret build_run_ctx_reset ctx:ctx_gpf_remote

    local d
    for d in /wd/dae /wd/wdae /wd/dae_conftests; do
      build_run_container ctx:ctx_gpf_remote bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .'
    done

    # build_run_attach ctx:ctx_gpf_remote bash

    # import genotype data
    {

      build_run_container ctx:ctx_gpf_remote bash -c '
      cd /wd/dae_conftests/dae_conftests/tests/fixtures/dae_iossifov2014 && \
      /opt/conda/bin/conda run --no-capture-output -n gpf \
        simple_study_import.py --id iossifov_2014 \
        -o /wd/import/data_iossifov_2014 \
        --denovo-file iossifov2014.txt \
        iossifov2014_families.ped'

      build_run_container ctx:ctx_gpf_remote bash -c '
      cat >> ./data/data-hg19-remote/studies/iossifov_2014/iossifov_2014.conf << EOT
[enrichment]
enabled = true
EOT'
    }

    # import phenotype data
    {
      build_run_container ctx:ctx_gpf_remote bash -c 'cd ./import/comp-data && /opt/conda/bin/conda run --no-capture-output -n gpf \
        simple_pheno_import.py -p comp_pheno.ped \
        -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno \
        --regression comp_pheno_regressions.conf'

      build_run_container ctx:ctx_gpf_remote sed -i '5i\\nphenotype_data="comp_pheno"' /wd/data/data-hg19-remote/studies/iossifov_2014/iossifov_2014.conf
    }

    # generate denovo gene sets
    {
      build_run_container ctx:ctx_gpf_remote bash -c '/opt/conda/bin/conda run --no-capture-output -n gpf \
        generate_denovo_gene_sets.py'
    }

    build_run_container ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf \
      /wd/wdae/wdae/wdaemanage.py migrate
    build_run_container ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf \
      /wd/wdae/wdae/wdae_create_dev_users.sh

    build_run_container_detached ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf \
      /wd/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010

    build_run_container ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf \
      /wd/scripts/wait-for-it.sh -h localhost -p 21010 -t 300

    build_run_ctx_persist ctx:ctx_gpf_remote
  }

  # lint
  build_stage "flake8"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_ctx_reset

    build_run_container bash -c '
      cd /wd; 
      /opt/conda/bin/conda run --no-capture-output -n gpf flake8 \
        --exit-zero \
        --format=pylint --max-complexity 15 \
        --inline-quotes=double --docstring-quotes=double --multiline-quotes=double \
        --exclude "*old*,*tmp*,*temp*,data-hg19*,gpf*,*build*" \
        --output-file=/wd/results/flake8_report . || true'

    build_run_local cp ./results/flake8_report ./test-results/
  }

  build_stage "pylint"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_ctx_reset

    build_run_container bash -c '
      cd /wd/; 
      wdae_files=$(find wdae/wdae -name "*.py");
      /opt/conda/bin/conda run --no-capture-output -n gpf 
      pylint dae/dae $wdae_files -f parseable --reports=no \
          --exit-zero > /wd/results/pylint_gpf_report || true'

    build_run_local cp ./results/pylint_gpf_report ./test-results/
  }

  build_stage "bandit"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_ctx_reset

    build_run_container bash -c '
      cd /wd/dae; 
      /opt/conda/bin/conda run --no-capture-output -n gpf \
      bandit --exit-zero \
        -r dae/ -o /wd/results/bandit_dae_report.html \
        -f html \
        --exclude "*tests/*" \
        -s B101 || true'

    build_run_container bash -c '
      cd /wd/wdae; 
      /opt/conda/bin/conda run --no-capture-output -n gpf \
      bandit --exit-zero \
        -r wdae/ -o /wd/results/bandit_wdae_report.html \
        -f html \
        --exclude "*tests/*" \
        -s B101 || true'

    build_run_local cp ./results/bandit_dae_report.html ./results/bandit_wdae_report.html ./test-results/
  }

  # mypy
  build_stage "MyPy"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_ctx_reset

    build_run_container bash -c '
      cd /wd/dae;
      /opt/conda/bin/conda run --no-capture-output -n gpf mypy dae \
          --exclude dae/docs/ \
          --exclude dae/docs/conf.py \
          --pretty \
          --warn-return-any \
          --warn-redundant-casts \
          --show-error-context \
          --no-incremental \
          --html-report /wd/results/mypy_dae_html_report \
          > /wd/results/mypy_dae_report || true'

    build_run_container bash -c '
      cd /wd/wdae;
      /opt/conda/bin/conda run --no-capture-output -n gpf mypy wdae \
          --exclude wdae/docs/ \
          --exclude wdae/docs/conf.py \
          --exclude wdae/conftest.py \
          --pretty \
          --warn-return-any \
          --warn-redundant-casts \
          --show-error-context \
          --no-incremental \
          --html-report /wd/results/mypy_wdae_html_report \
          > /wd/results/mypy_wdae_report || true'

      build_run_local cp ./results/mypy_dae_report ./results/mypy_wdae_report ./test-results/
      build_run_local cp -r ./results/mypy_dae_html_report ./results/mypy_wdae_html_report ./test-results/
  }

  # import test data to impala
  build_stage "Import test data to impala"
  {

    build_run_ctx_init "container" "${gpf_dev_image_ref}" \
      --network "${ctx_network["network_id"]}" \
      --env DAE_DB_DIR="/wd/data/data-hg19-startup/" \
      --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
      --env TEST_REMOTE_HOST="gpfremote" \
      --env DAE_HDFS_HOST="impala" \
      --env DAE_IMPALA_HOST="impala"

    defer_ret build_run_ctx_reset

    for d in /wd/dae /wd/wdae /wd/dae_conftests; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf \
        pip install -e .'
    done

  }

  # Tests - dae
  build_stage "Tests - dae"
  {

    build_run_ctx_init "container" "${gpf_dev_image_ref}" \
      --network "${ctx_network["network_id"]}" \
      --env DAE_DB_DIR="/wd/data/data-hg19-startup/" \
      --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
      --env TEST_REMOTE_HOST="gpfremote" \
      --env DAE_HDFS_HOST="impala" \
      --env DAE_IMPALA_HOST="impala"

    defer_ret build_run_ctx_reset

    for d in /wd/dae /wd/wdae /wd/dae_conftests; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf \
        pip install -e .'
    done

    build_run_container bash -c '
        cd /wd/dae;
        export PYTHONHASHSEED=0;
        /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v \
           --durations 20 \
          --cov-config /wd/coveragerc \
          --junitxml=/wd/results/dae-junit.xml \
          --cov dae \
          dae/ || true'

    build_run_local cp ./results/dae-junit.xml ./test-results/
  }

  # Tests - wdae
  build_stage "Tests - wdae"
  {

    build_run_ctx_init "container" "${gpf_dev_image_ref}" \
      --network "${ctx_network["network_id"]}" \
      --env DAE_DB_DIR="/wd/data/data-hg19-startup/" \
      --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml" \
      --env TEST_REMOTE_HOST="gpfremote" \
      --env DAE_HDFS_HOST="impala" \
      --env DAE_IMPALA_HOST="impala"

    defer_ret build_run_ctx_reset

    for d in /wd/dae /wd/wdae /wd/dae_conftests; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf \
        pip install -e .'
    done

    build_run_container bash -c '
        cd /wd/wdae;
        export PYTHONHASHSEED=0;
        /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v \
          --durations 20 \
          --cov-config /wd/coveragerc \
          --junitxml=/wd/results/wdae-junit.xml \
          --cov wdae \
          wdae || true'

    build_run_container coverage combine dae/.coverage wdae/.coverage
    build_run_container coverage xml
    build_run_container coverage html --title GPF -d ./test-results/coverage-html

    build_run_container cp ./results/wdae-junit.xml coverage.xml ./test-results/
  }

  build_stage "Sonarqube"
  {
    local gpf_git_branch=$(e gpf_git_branch)

    build_run_local echo "gpf_git_branch=$gpf_git_branch"
    build_run_local echo "SONARQUBE_DEFAULT_TOKEN=$SONARQUBE_DEFAULT_TOKEN"

    if [ "$SONARQUBE_DEFAULT_TOKEN" != "" ] && [ "$gpf_git_branch" = "master" ]; then
      build_run_local echo "Sonarqube stage started"

      build_run_local docker run --rm \
          -e SONAR_HOST_URL="http://sonarqube.seqpipe.org:9000" \
          -e SONAR_LOGIN="${SONARQUBE_DEFAULT_TOKEN}" \
          -v "$(pwd):/usr/src" \
          sonarsource/sonar-scanner-cli \
          -Dsonar.projectKey=gpf \
          -Dsonar.python.version=3.9 \
          -Dsonar.python.coverage.reportPaths="coverage.xml"

    else
      build_run_local echo "Sonarqube stage skipped"
    fi
  }

  build_stage "Package"
  {
    build_run_ctx_init "container" "ubuntu:20.04"
    defer_ret build_run_ctx_reset

    local gpf_tag=$(e gpf_tag)
    build_run echo "${gpf_tag}"
    local __gpf_build_no=$(e __gpf_build_no)
    build_run echo ${__gpf_build_no}

    build_run bash -c '
      echo "build = \"'"${gpf_tag}"'-'"${__gpf_build_no}"'\"" > dae/dae/__build__.py
    '
    build_run bash -c '
      echo "build = \"'"${gpf_tag}"'-'"${__gpf_build_no}"'\"" > wdae/wdae/__build__.py
    '


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
          --exclude dae/.coverage \
          --exclude dae/tmp \
          --exclude dae/build \
          --exclude wdae/build \
          --exclude tests \
          --exclude dask-worker-space \
          --exclude demo-scripts \
          --exclude TESTphastCons100way.bedGraph.gz.tbi \
          --exclude conftest.py \
          --exclude gpf_wdae.egg-info \
          --transform "s,^,gpf/," \
          dae/ wdae/ environment.yml dev-environment.yml VERSION
    )
  }

  # post cleanup
  build_stage "Post Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:20.04"
    defer_ret build_run_ctx_reset
    build_run rm -rvf ./data/ ./import/ ./downloads ./results
  }
}

main "$@"
