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

  libmain_init iossifovlab.gpf_documentation gpf_documentation
  libmain_init_build_env \
    clobber:"$clobber" preset:"$preset" build_no:"$build_no" \
    generate_jenkins_init:"$generate_jenkins_init" expose_ports:"$expose_ports" \
    iossifovlab.gpf iossifovlab.data-hg19-startup

  libmain_save_build_env_on_exit
  libbuild_init stage:"$stage" registry.seqpipe.org

  liblog_verbosity=6

  defer_ret build_run_ctx_reset_all_persistent

  # cleanup
  build_stage "Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:20.04"
    defer_ret build_run_ctx_reset

    build_run rm -rvf ./data/ ./import/ ./downloads ./results ./gpf
    build_run_local mkdir -p ./data/ ./import/ ./downloads ./results ./cache
  }


  build_stage "Get GPF source"
  {
    local gpf_package_image
    gpf_package_image=$(e docker_data_img_gpf_package)

    # copy gpf package
    build_run_local mkdir -p ./iossifovlab-gpf/gpf
    build_docker_image_cp_from "$gpf_package_image" ./gpf/ /gpf
  }

  # prepare gpf data
  build_stage "Get GPF data instance"
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

#   # run impala
#   build_stage "Run impala"
#   {
#     # create network
#     {
#       local -A ctx_network
#       build_run_ctx_init ctx:ctx_network "persistent" "network"
#       build_run_ctx_persist ctx:ctx_network
#     }
#     # setup impala
#     {
#       local -A ctx_impala
#       build_run_ctx_init ctx:ctx_impala "persistent" "container" "seqpipe/seqpipe-docker-impala:latest" \
#           "cmd-from-image" "no-def-mounts" \
#           ports:21050,8020,25000,25010,25020 --hostname impala --network "${ctx_network["network_id"]}"

#       defer_ret build_run_ctx_reset ctx:ctx_impala

#       build_run_container ctx:ctx_impala /wait-for-it.sh -h localhost -p 21050 -t 300

#       build_run_ctx_persist ctx:ctx_impala
#     }
#   }

  build_stage "Build documentation"
  {

    local gpf_dev_image_ref;
    gpf_dev_image_ref=$(e docker_img_gpf_dev)

    build_run_ctx_init "container" "${gpf_dev_image_ref}" \
      --env DAE_DB_DIR="/wd/data/data-hg19-startup/" \
      --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml"

    defer_ret build_run_ctx_reset

    local d
    for d in /wd/gpf/dae /wd/gpf/wdae; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install .'
    done

    build_run_container cd /wd/gpf/dae/dae/docs 
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        sphinx-build -b html -d _build/doctrees   . _build/html"
    build_run_container tar zcvf /wd/results/gpf-dae-html.tar.gz -C _build/ html/

    build_run_container cd /wd/gpf/wdae/wdae/docs 
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        sphinx-build -b html -d _build/doctrees   . _build/html"
    build_run_container tar zcvf /wd/results/gpf-wdae-html.tar.gz -C _build/ html/

    build_run_container cd /wd/userdocs
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        sphinx-build -b html -d _build/doctrees   . _build/html"
    build_run_container tar zcvf /wd/results/gpf-user-html.tar.gz -C _build/ html/

  }

  build_stage "Publish documentation"
  {

    local iossifovlab_anaconda_infra_ref;
    iossifovlab_anaconda_infra_ref=$(e docker_img_iossifovlab_anaconda_infra)

    build_run_ctx_init "container" "${iossifovlab_anaconda_infra_ref}"
    defer_ret build_run_ctx_reset

    # copy host's .ssh dir as the root .ssh in the container
    build_run_container_cp_to /root/ $HOME/.ssh
    build_run_container chown -R root:root /root/.ssh
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        ansible-playbook -i doc_inventory doc_publish.yml"

  }

}

main "$@"
