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
    stage:all preset:fast clobber:allow_if_matching_values build_no:0 generate_jenkins_init:no expose_ports:no -- "$@"

  local preset="${options["preset"]}"
  local stage="${options["stage"]}"
  local clobber="${options["clobber"]}"
  local build_no="${options["build_no"]}"
  local generate_jenkins_init="${options["generate_jenkins_init"]}"
  local expose_ports="${options["expose_ports"]}"

  libmain_init iossifovlab.gpf gpf
  libmain_init_build_env \
    clobber:"$clobber" preset:"$preset" build_no:"$build_no" generate_jenkins_init:"$generate_jenkins_init" expose_ports:"$expose_ports" \
    seqpipe.data-hg19-startup
  libmain_save_build_env_on_exit
  libbuild_init stage:"$stage" registry.seqpipe.org

  libmain_validate_bumped_and_git_versions

  defer_ret build_run_ctx_reset_all_persistent

  # cleanup
  build_stage "Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:18.04"
    defer_ret build_run_ctx_reset

    build_run rm -rvf ./data/ ./import/ ./downloads ./results
    build_run_local mkdir ./data/ ./import/ ./downloads ./results

    build_run_local rm -rvf ./test-results/
    build_run_local mkdir -p ./test-results/

  }

  local gpf_dev_image="gpf-dev"
  local gpf_dev_image_ref
  # create gpf docker image
  build_stage "Create gpf-dev docker image"
  {
    local docker_img_seqpipe_anaconda_base_tag
    docker_img_seqpipe_anaconda_base_tag="$(e docker_img_seqpipe_anaconda_base_tag)"
    build_docker_image_create "$gpf_dev_image" . ./Dockerfile "$docker_img_seqpipe_anaconda_base_tag"
    gpf_dev_image_ref="$(e docker_img_gpf_dev)"
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
    build_run_local sed -i \
      -e s/"^impala\.host.*$/impala.hosts = \[\"impala\"\]/"g \
      -e s/"^hdfs\.host.*$/hdfs.host = \"impala\"/"g \
      ./data/data-hg19-startup/DAE.conf

    build_run_ctx_init "container" "ubuntu:18.04"
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

  build_stage "Prepare GPF remote data"
  {

    # same as GPF data but in different dir
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
      build_run_local sed -i \
        -e s/"^impala\.host.*$/impala.hosts = \[\"impala\"\]/"g \
        -e s/"^hdfs\.host.*$/hdfs.host = \"impala\"/"g \
        ./data/data-hg19-remote/DAE.conf

      build_run_ctx_init "container" "ubuntu:18.04"
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

      # GPF remote specific fixup
      {
        build_run_local sed -i \
          -e s/"^instance_id.*$/instance_id = \"data_hg19_remote\"/"g \
          ./data/data-hg19-remote/DAE.conf
      }
    }

    # import data for gpf remote
    {
      # use the freshly built gpf image
      build_run_ctx_init "container" "$gpf_dev_image_ref"
      defer_ret build_run_ctx_reset

      # setup python env
      {
        build_run bash -c 'cd /wd/dae && /opt/conda/bin/conda run --no-capture-output -n gpf pip install .'
        build_run bash -c 'cd /wd/wdae && /opt/conda/bin/conda run --no-capture-output -n gpf pip install .'
        build_run bash -c 'cd /wd/dae_conftests && /opt/conda/bin/conda run --no-capture-output -n gpf pip install .'
      }

      # import genotype data
      {
        local docker_data_img_genotype_iossifov_2014
        docker_data_img_genotype_iossifov_2014="$(e docker_data_img_genotype_iossifov_2014)"

        # copy data
        build_run_local mkdir -p ./import
        build_docker_image_cp_from "$docker_data_img_genotype_iossifov_2014" ./import /

        build_run bash -c 'export DAE_DB_DIR="/wd/data/data-hg19-remote"; cd ./import/iossifov_2014 && /opt/conda/bin/conda run --no-capture-output -n gpf simple_study_import.py --id iossifov_2014 \
          -o ./data_iossifov_2014 \
          --denovo-file IossifovWE2014.tsv \
          IossifovWE2014.ped'

        build_run_container bash -c 'cat >> ./data/data-hg19-remote/studies/iossifov_2014/iossifov_2014.conf << EOT

      [enrichment]
      enabled = true
EOT'
      }

      # import phenotype data
      {
        local docker_data_img_phenotype_comp_data
        docker_data_img_phenotype_comp_data="$(e docker_data_img_phenotype_comp_data)"

        # copy data
        build_docker_image_cp_from "$docker_data_img_phenotype_comp_data" ./import /

        build_run bash -c 'export DAE_DB_DIR="/wd/data/data-hg19-remote"; cd ./import/comp-data && /opt/conda/bin/conda run --no-capture-output -n gpf simple_pheno_import.py -p comp_pheno.ped \
          -i instruments/ -d comp_pheno_data_dictionary.tsv -o comp_pheno \
          --regression comp_pheno_regressions.conf'

        build_run_container sed -i '5i\\nphenotype_data="comp_pheno"' /wd/data/data-hg19-remote/studies/iossifov_2014/iossifov_2014.conf
      }

      # generate denovo gene sets
      {
        build_run_container bash -c 'export DAE_DB_DIR="/wd/data/data-hg19-remote"; /opt/conda/bin/conda run --no-capture-output -n gpf generate_denovo_gene_sets.py'
      }
    }

    # run cluster
    build_stage "Run cluster"
    {
      # create network
      local -A ctx_network
      build_run_ctx_init ctx:ctx_network "persistent" "network"
      build_run_ctx_persist ctx:ctx_network

      #      # setup mysql
      #      {
      #        local -A ctx_mysql
      #        build_run_init ctx:ctx_mysql "container" "mysql:5.7" "cmd-from-image" \
      #          --hostname mysql \
      #          --network "${ctx_network["network_id"]}" \
      #          --env MYSQL_DATABASE=gpf \
      #          --env MYSQL_USER=seqpipe \
      #          --env MYSQL_PASSWORD=secret \
      #          --env MYSQL_ROOT_PASSWORD=secret \
      #          --env MYSQL_PORT=3306 \
      #          -- \
      #          --character-set-server=utf8 --collation-server=utf8_bin
      #
      #        defer_ret build_run_ctx_reset ctx:ctx_mysql
      #
      #        build_run_container ctx:ctx_mysql /wd/scripts/wait-for-it.sh -h mysql -p 3306 -t 300
      #
      #        build_run_container ctx:ctx_mysql mysql -u root -psecret -h mysql \
      #          -e "CREATE DATABASE IF NOT EXISTS test_gpf"
      #
      #        build_run_container ctx:ctx_mysql mysql -u root -psecret -h mysql \
      #          -e "GRANT ALL PRIVILEGES ON test_gpf.* TO 'seqpipe'@'%' IDENTIFIED BY 'secret' WITH GRANT OPTION"
      #      }

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

      # setup gpf remote
      {
        local -A ctx_gpf_remote
        build_run_ctx_init ctx:ctx_gpf_remote "persistent" "container" "${gpf_dev_image_ref}" \
          ports:21010 \
          --hostname gpfremote \
          --network "${ctx_network["network_id"]}" \
          --env DAE_DB_DIR="/data/data-hg19-remote/"
        defer_ret build_run_ctx_reset ctx:ctx_gpf_remote

        local d
        for d in /wd/dae /wd/wdae /wd/dae_conftests; do
          build_run_container ctx:ctx_gpf_remote bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .'
        done

        build_run_container ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf /wd/wdae/wdae/wdaemanage.py migrate
        build_run_container ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf /wd/wdae/wdae/wdae_create_dev_users.sh

        build_run_container_detached ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf /wd/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010

        build_run_container ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf /wd/scripts/wait-for-it.sh -h localhost -p 21010 -t 300

        build_run_ctx_persist ctx:ctx_gpf_remote
      }
    }
  }

  # import test data to impala
  build_stage "Import test data to impala"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}" \
      --network "${ctx_network["network_id"]}" \
      --env DAE_DB_DIR="/data/data-hg19-remote/" \
      --env TEST_REMOTE_HOST="gpfremote" \
      --env DAE_HDFS_HOST="impala" \
      --env DAE_IMPALA_HOST="impala"
    defer_ret build_run_ctx_reset

    for d in /wd/dae /wd/wdae /wd/dae_conftests; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .'
    done

    # build_run_container bash -c 'cd /wd/dae_conftests; /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v --reimport --no-cleanup dae_conftests/tests/'
    # build_run_container bash -c 'cd /wd/dae; /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v --no-cleanup dae/gene/tests/test_denovo_gene_sets_db.py'
    # build_run_container bash -c 'cd /wd/dae; /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v --no-cleanup dae/backends/tests/test_cnv_variants.py::test_cnv_impala'
  }

  # lint
  build_stage "Lint"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_ctx_reset

    build_run_container bash -c 'cd /wd; flake8 --format=pylint --output-file=/wd/results/flake8_report --exclude "*old*,*tmp*,*temp*,data-hg19*,gpf*" . || true'

    build_run_local cp ./results/flake8_report ./test-results/
  }

  # mypy
  build_stage "Type Check"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_ctx_reset

    build_run_container bash -c '
      cd /wd/dae;
      /opt/conda/bin/conda run --no-capture-output -n gpf mypy dae \
          --exclude dae/docs/ \
          --exclude dae/docs/conf.py \
          --pretty \
          --ignore-missing-imports \
          --warn-return-any \
          --warn-redundant-casts \
          > /wd/results/mypy_dae_report || true'

    build_run_container bash -c '
      cd /wd/wdae;
      /opt/conda/bin/conda run --no-capture-output -n gpf mypy wdae \
          --exclude wdae/docs/ \
          --exclude wdae/docs/conf.py \
          --exclude wdae/conftest.py \
          --pretty \
          --ignore-missing-imports \
          --warn-return-any \
          --warn-redundant-casts \
          > /wd/results/mypy_wdae_report || true'

      build_run_local cp ./results/mypy_dae_report ./results/mypy_wdae_report ./test-results/
  }

  # Tests - dae
  build_stage "Tests - dae"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}" \
      --network "${ctx_network["network_id"]}" \
      --env DAE_DB_DIR="/data/data-hg19-startup/" \
      --env TEST_REMOTE_HOST="gpfremote" \
      --env DAE_HDFS_HOST="impala" \
      --env DAE_IMPALA_HOST="impala"
    defer_ret build_run_ctx_reset

    for d in /wd/dae /wd/wdae /wd/dae_conftests; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .'
    done

    build_run_container bash -c '
        cd /wd/dae;
        export PYTHONHASHSEED=0;
        /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v --reimport --durations 20 \
          --cov-config /wd/coveragerc \
          --junitxml=/wd/results/dae-junit.xml \
          --cov-report=html:/wd/results/dae-coverage.html \
          --cov-report=xml:/wd/results/dae-coverage.xml \
          --cov /wd/dae/ \
          dae/ || true'

    build_run_local cp ./results/dae-junit.xml ./results/dae-coverage.xml ./test-results/
  }

  # Tests - wdae
  build_stage "Tests - wdae"
  {
    build_run_ctx_init "container" "${gpf_dev_image_ref}" \
      --network "${ctx_network["network_id"]}" \
      --env DAE_DB_DIR="/data/data-hg19-startup/" \
      --env TEST_REMOTE_HOST="gpfremote" \
      --env DAE_HDFS_HOST="impala" \
      --env DAE_IMPALA_HOST="impala"
    defer_ret build_run_ctx_reset

    for d in /wd/dae /wd/wdae /wd/dae_conftests; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .'
    done

    build_run_container bash -c '
        cd /wd/wdae;
        export PYTHONHASHSEED=0;
        /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v --no-cleanup --durations 20 \
          --cov-config /wd/coveragerc \
          --junitxml=/wd/results/wdae-junit.xml \
          --cov-report=html:/wd/results/wdae-coverage.html \
          --cov-report=xml:/wd/results/wdae-coverage.xml \
          --cov /wd/wdae/ \
          wdae || true'

    build_run_local cp ./results/wdae-junit.xml ./results/wdae-coverage.xml ./test-results/
  }

  # post cleanup
  build_stage "Post Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:18.04"
    defer_ret build_run_ctx_reset
    build_run rm -rvf ./data/ ./import/ ./downloads ./results
  }
}

main "$@"
