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
# shellcheck source=build-scripts/libdefer.sh
include liblog.sh

function main() {
  local stage="${1-all}"

  libmain_init gpf gpf
  libmain_init_build_env seqpipe-containers data-hg19-startup
  libmain_save_build_env_on_exit
  libbuild_init "$stage" registry.seqpipe.org

  # parse version and run validation checks
  {

    function main_parse_major() {
      local major
      major="$(sed -e 's/^\([^.]\+\).\([^.]\+\).*$/\1/' <<<"$1")"

      if ! check_digits "$major"; then
        crit "failed to extract major version: got: '$major' from '$1'"
        return 1
      fi
    }

    function main_parse_minor() {
      local minor
      minor="$(sed -e 's/^\([^.]\+\).\([^.]\+\).*$/\2/' <<<"$1")"

      if ! check_digits "$minor"; then
        crit "failed to extract minor version: got: '$minor' from '$1'"
        return 1
      fi
    }

    # parse the defined version in the repo
    {
      local version
      version="$(cat VERSION)"
      notify "local version is: $version"

      local version_major
      version_major="$(main_parse_major "$version")"

      local version_minor
      version_minor="$(main_parse_minor "$version")"
    }

    # parse the version according to git
    {
      local git_version
      git_version="$(ee git_describe)"

      notify "git version is: $git_version"

      local git_version_major
      git_version_major="$(main_parse_major "${git_version#v}")"

      local git_version_minor
      git_version_minor="$(main_parse_minor "${git_version#v}")"
    }

    # error out if there's difference between the major and the minor versions of the two differently obtained versions
    {
      if [ "$version_major" != "$git_version_major" ]; then
        crit "difference in major version between VERSION file and latest git tag: $version_major vs $git_version_major"
        return 1
      fi

      if [ "$version_minor" != "$git_version_minor" ]; then
        crit "difference in minor version between VERSION file and latest git tag: $version_minor vs $git_version_minor"
        return 1
      fi
    }
  }

  # cleanup
  build_stage "Cleanup"
  {
    build_run_init "container" "ubuntu:18.04"
    defer_ret build_run_reset

    build_run rm -rf ./data/ ./import/ ./downloads ./results
    build_run_local mkdir ./data/ ./import/ ./downloads ./results
  }

  build_run_init "local"
  defer_ret build_run_reset

  local gpf_dev_image="gpf-dev"

  # create gpf docker image
  build_stage "Create $gpf_dev_image docker image"
  {
    build_docker_image_create "$gpf_dev_image" . ./Dockerfile
  }

  # prepare gpf data
  build_stage "Prepare GPF data"
  {
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

    build_run_init "container" "ubuntu:18.04"

    # cleanup
    build_run_container rm -rf \
      ./data/data-hg19-startup/studies/* \
      ./data/data-hg19-startup/pheno/* \
      ./data/data-hg19-startup/wdae/wdae.sql

    build_run_reset

    build_run_init "local"

    # setup directory structure
    build_run_local mkdir -p \
      ./data/data-hg19-startup/genomic-scores-hg19 \
      ./data/data-hg19-startup/genomic-scores-hg38 \
      ./data/data-hg19-startup/wdae
  }

  build_stage "Prepare GPF remote data"
  {
    local data_hg19_startup_image_ref
    data_hg19_startup_image_ref="$(e docker_data_img_data_hg19_startup)"

    # same as GPF data but in different dir
    {
      # copy data
      build_run_local mkdir -p ./data/data-hg19-remote
      build_docker_image_cp_from "$data_hg19_startup_image_ref" ./data/data-hg19-remote /

      # reset instance conf
      build_run_local sed -i \
        -e s/"^impala\.host.*$/impala.hosts = \[\"impala\"\]/"g \
        -e s/"^hdfs\.host.*$/hdfs.host = \"impala\"/"g \
        ./data/data-hg19-remote/DAE.conf

      build_run_init "container" "ubuntu:18.04"

      # cleanup
      build_run_container rm -rf \
        ./data/data-hg19-startup/studies/* \
        ./data/data-hg19-startup/pheno/* \
        ./data/data-hg19-startup/wdae/wdae.sql

      build_run_reset

      build_run_init "local"
      defer_ret build_run_reset

      # setup directory structure
      build_run_local mkdir -p \
        ./data/data-hg19-remote/genomic-scores-hg19 \
        ./data/data-hg19-remote/genomic-scores-hg38 \
        ./data/data-hg19-remote/wdae
    }

    # GPF remote specific fixup
    {
      build_run_local sed -i \
        -e s/"^instance_id.*$/instance_id = \"data_hg19_remote\"/"g \
        ./data/data-hg19-remote/DAE.conf
    }

    # import data for gpf remote
    {
      local gpf_dev_image_ref
      gpf_dev_image_ref="$(e docker_img_gpf_dev)"
      build_run_init "container" "$gpf_dev_image_ref"
      defer_ret build_run_reset

      # fixup /code to point to /wd
      {
        build_run_container bash -c 'rmdir /code && ln -s /wd /code'
      }

      # setup python env
      {
        build_run bash -c 'cd /code/dae && /opt/conda/bin/conda run --no-capture-output -n gpf pip install .'
        build_run bash -c 'cd /code/wdae && /opt/conda/bin/conda run --no-capture-output -n gpf pip install .'
        build_run bash -c 'cd /code/dae_conftests && /opt/conda/bin/conda run --no-capture-output -n gpf pip install .'
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

      build_run_reset
    }

    # run cluster
    build_stage "Run cluster"
    {
      # create network
      docker network create -d bridge hr_temp
      defer_ret docker network rm hr_temp

#      # setup mysql
#      {
#        local -A ctx_mysql
#        build_run_init ctx:ctx_mysql "container" "mysql:5.7" "cmd-from-image" \
#          --hostname=mysql \
#          --network=hr_temp \
#          --env MYSQL_DATABASE=gpf \
#          --env MYSQL_USER=seqpipe \
#          --env MYSQL_PASSWORD=secret \
#          --env MYSQL_ROOT_PASSWORD=secret \
#          --env MYSQL_PORT=3306 \
#          -- \
#          --character-set-server=utf8 --collation-server=utf8_bin
#
#        defer_ret build_run_reset ctx:ctx_mysql
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
        build_run_init ctx:ctx_impala "container" "seqpipe/seqpipe-docker-impala:latest" "cmd-from-image" --hostname=impala --network=hr_temp
        defer_ret build_run_reset ctx:ctx_impala

        build_run_container ctx:ctx_impala /wd/scripts/wait-for-it.sh -h localhost -p 21050 -t 300
      }

      # setup gpf remote
      {
        local -A ctx_gpf_remote
        build_run_init ctx:ctx_gpf_remote "container" "${gpf_dev_image_ref}" \
          --hostname=gpfremote \
          --network=hr_temp \
          --env DAE_DB_DIR="/data/data-hg19-remote/"
        defer_ret build_run_reset ctx:ctx_gpf_remote

        # fixup /code to point to /wd
        {
          build_run_container ctx:ctx_gpf_remote bash -c 'rmdir /code && ln -s /wd /code'
        }

        local d
        for d in /code/dae /code/wdae /code/dae_conftests; do
          build_run_container ctx:ctx_gpf_remote bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .'
        done

        build_run_container ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf /code/wdae/wdae/wdaemanage.py migrate
        build_run_container ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf /code/wdae/wdae/wdae_create_dev_users.sh

        build_run_container_detached ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf /code/wdae/wdae/wdaemanage.py runserver 0.0.0.0:21010

        build_run_container ctx:ctx_gpf_remote /opt/conda/bin/conda run --no-capture-output -n gpf /code/scripts/wait-for-it.sh -h localhost -p 21010 -t 300
      }
    }

    # import test data to impala
    build_stage "Import test data to impala"
    {
      build_run_init "container" "${gpf_dev_image_ref}" \
        --network=hr_temp \
        --env DAE_DB_DIR="/data/data-hg19-remote/" \
        --env TEST_REMOTE_HOST="gpfremote" \
        --env DAE_HDFS_HOST="impala" \
        --env DAE_IMPALA_HOST="impala"
      defer_ret build_run_reset

      # fixup /code to point to /wd
      {
        build_run_container bash -c 'rmdir /code && ln -s /wd /code'
      }

      for d in /code/dae /code/wdae /code/dae_conftests; do
        build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .'
      done

      build_run_container bash -c 'cd /code/dae_conftests; /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v --reimport --no-cleanup dae_conftests/tests/'

      build_run_container bash -c 'cd /code/dae; /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v --no-cleanup dae/gene/tests/test_denovo_gene_sets_db.py'
      build_run_container bash -c 'cd /code/dae; /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v --no-cleanup dae/backends/tests/test_cnv_variants.py::test_cnv_impala'
    }
  }

  # lint
  build_stage "Lint"
  {
    build_run_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_reset

    # fixup /code to point to /wd
    {
      build_run_container bash -c 'rmdir /code && ln -s /wd /code'
    }

    build_run_container bash -c 'cd /code; flake8 --format=html --htmldir=/code/results/flake8_report --exclude "--exclude \"*old*,*tmp*,*temp*,data-hg19*,gpf*\"" . || true'
  }

  # mypy
  build_stage "Type Check"
  {
    build_run_init "container" "${gpf_dev_image_ref}"
    defer_ret build_run_reset

    # fixup /code to point to /wd
    {
      build_run_container bash -c 'rmdir /code && ln -s /wd /code'
    }

    build_run_container bash -c '
      cd /code/dae;
      /opt/conda/bin/conda run --no-capture-output -n gpf mypy dae \
          --exclude dae/docs/ \
          --exclude dae/docs/conf.py \
          --pretty \
          --ignore-missing-imports \
          --warn-return-any \
          --warn-redundant-casts \
          --html-report /code/results/mypy/dae_report || true'

    build_run_container bash -c '
      cd /code/wdae;
      /opt/conda/bin/conda run --no-capture-output -n gpf mypy wdae \
          --exclude wdae/docs/ \
          --exclude wdae/docs/conf.py \
          --exclude wdae/conftest.py \
          --pretty \
          --ignore-missing-imports \
          --warn-return-any \
          --warn-redundant-casts \
          --html-report /code/results/mypy/wdae_report || true'
  }

  # Tests - dae
  build_stage "Tests - dae"
  {
    build_run_init "container" "${gpf_dev_image_ref}" \
      --network=hr_temp \
      --env DAE_DB_DIR="/data/data-hg19-startup/" \
      --env TEST_REMOTE_HOST="gpfremote" \
      --env DAE_HDFS_HOST="impala" \
      --env DAE_IMPALA_HOST="impala"
    defer_ret build_run_reset

    # fixup /code to point to /wd
    {
      build_run_container bash -c 'rmdir /code && ln -s /wd /code'
    }

    for d in /code/dae /code/wdae /code/dae_conftests; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .'
    done

    build_run_container bash -c '
        cd /code/dae;
        export PYTHONHASHSEED=0;
        /opt/conda/bin/conda run --no-capture-output -n gpf py.test -v --no-cleanup -n 10 \
          --cov-config /code/coveragerc \
          --junitxml=/code/results/dae-junit.xml \
          --cov-report=html:/code/results/dae-coverage.html \
          --cov-report=xml:/code/results/dae-coverage.xml \
          --cov /code/dae/ \
          dae/'
  }

  # Tests - wdae
  build_stage "Tests - wdae"
  {
    build_run_init "container" "${gpf_dev_image_ref}" \
      --network=hr_temp \
      --env DAE_DB_DIR="/data/data-hg19-startup/" \
      --env TEST_REMOTE_HOST="gpfremote" \
      --env DAE_HDFS_HOST="impala" \
      --env DAE_IMPALA_HOST="impala"
    defer_ret build_run_reset

    # fixup /code to point to /wd
    {
      build_run_container bash -c 'rmdir /code && ln -s /wd /code'
    }

    for d in /code/dae /code/wdae /code/dae_conftests; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install -e .'
    done

    build_run_container bash -c '
        cd /code/wdae;
        export PYTHONHASHSEED=0;
        /opt/conda/bin/conda run --no-capture-output -n gpf py.test --no-cleanup -v -n 10 \
          --cov-config /code/coveragerc \
          --junitxml=/code/results/wdae-junit.xml \
          --cov-report=html:/code/results/wdae-coverage.html \
          --cov-report=xml:/code/results/wdae-coverage.xml \
          --cov /code/wdae/ \
          wdae'

    build_run_local rm -r ./test-results/
    build_run_local mkdir -p ./test-results/
    build_run_local cp ./results/wdae-junit.xml ./results/dae-junit.xml ./test-results/
  }

  # post cleanup
  build_stage "Post Cleanup"
  {
    build_run_init "container" "ubuntu:18.04"
    build_run rm -rf ./data/ ./import/ ./downloads ./results
  }
}

main "$@"
