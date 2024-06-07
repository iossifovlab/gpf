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
    iossifovlab.gpf-release

  libmain_save_build_env_on_exit
  libbuild_init stage:"$stage" registry.seqpipe.org

  liblog_verbosity=6

  defer_ret build_run_ctx_reset_all_persistent


  build_stage "Draw dependencies"
  {
    build_deps_graph_write_image 'build-env/dependency-graph.svg'
  }

  local gpf_release_version
  gpf_release_version="$(e "gpf_release_gpf_release_version")"

  # cleanup
  build_stage "Cleanup"
  {
    build_run_ctx_init "container" "ubuntu:22.04"
    defer_ret build_run_ctx_reset

    build_run rm -rf ./data/ ./results ./gpf
    build_run rm -rf ./userdocs/gpf

    build_run_local mkdir -p ./data/ ./results ./cache
  }


  build_stage "Get GPF source"
  {
    local image_ref
    image_ref="$(e docker_img_iossifovlab_mamba_base)"
    build_run_ctx_init "container" "$image_ref"
    defer_ret build_run_ctx_reset


    build_run bash -c 'mkdir -p /root/.ssh'

    build_run_container_cp_to "/root/.gitconfig" "${HOME}/.gitconfig"
    build_run_container_cp_to "/root/.ssh/id_rsa" "${HOME}/.ssh/jenkins_rsa"
    build_run bash -c 'chown 400 /root/.ssh/id_rsa'
    build_run bash -c 'cat > /root/.ssh/config << EOT
Host github.com
    StrictHostKeyChecking no

EOT
'
    build_run mkdir -p projects


    # the quotes around 'EOF' are signifcant - it forces bash to treat the string as literal string until EOF
    build_run bash -e -x <<'EOF'
    if ! [ -d "projects/gpf.repo" ]; then
        git clone "ssh://git@github.com/iossifovlab/gpf" "projects/gpf.repo"
    fi
EOF

    # the quotes around 'EOF' are signifcant - it forces bash to treat the string as literal string until EOF
    build_run env gpf_release_version="${gpf_release_version}" bash -e -x << 'EOF'

        cd "projects/gpf.repo"
        git checkout master
        git pull --ff-only
        git checkout "${gpf_release_version}"
        cd -
EOF
  }

  # prepare gpf data
  build_stage "Prepare GPF data instance"
  {
    build_run_ctx_init "local"
    defer_ret build_run_ctx_reset

    # create GPF instance
    build_run_local mkdir -p ./data/data-hg38-hello
        build_run_local bash -c 'cat > ./data/data-hg38-hello/gpf_instance.yaml << EOT
instance_id: "hg38_hello"

reference_genome:
    resource_id: "hg38/genomes/GRCh38-hg38"

gene_models:
    resource_id: "hg38/gene_models/refSeq_v20200330"
EOT
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
    build_run_ctx_init "container" "ubuntu:22.04"
    defer_ret build_run_ctx_reset

  }

  build_stage "Build documentation"
  {

    local gpf_dev_image_ref;
    gpf_dev_image_ref=$(e docker_img_gpf_dev)

    build_run_ctx_init "container" "${gpf_dev_image_ref}" \
      --env gpf_release_version="${gpf_release_version}" \
      --env DAE_DB_DIR="/wd/data/data-hg38-hello/" \
      --env GRR_DEFINITION_FILE="/wd/cache/grr_definition.yaml"

    defer_ret build_run_ctx_reset

    build_run_container cd /wd/userdocs
    build_run_container ln -sf ../projects/gpf.repo gpf
  
    local d
    for d in /wd/projects/gpf.repo/dae /wd/projects/gpf.repo/wdae; do
      build_run_container bash -c 'cd "'"${d}"'"; /opt/conda/bin/conda run --no-capture-output -n gpf pip install .'
    done

    build_run_container cd /wd/userdocs/gpf/dae/dae/docs 
    build_run_container rm -rf modules
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        sphinx-apidoc -o modules .. docs tests"
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        sphinx-build -d _build/doctrees   . _build/html"
    # build_run_container tar zcvf /wd/results/gpf-dae-html.tar.gz -C _build/ html/

    build_run_container cd /wd/userdocs/gpf/wdae/wdae/docs 
    build_run_container rm -rf modules
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        sphinx-apidoc -o modules .. docs tests"
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        /wd/userdocs/gpf/wdae/wdae/docs/api_docs_generator.py \
        --root_dir /wd/userdocs/gpf/wdae/wdae \
        --output_dir /wd/userdocs/gpf/wdae/wdae/docs/routes"
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        sphinx-build -d _build/doctrees   . _build/html"
    # build_run_container tar zcvf /wd/results/gpf-wdae-html.tar.gz -C _build/ html/

    build_run_container cd /wd/userdocs
    build_run_container bash -c "
        /opt/conda/bin/conda run --no-capture-output -n gpf \
        sphinx-build -d _build/doctrees   . _build/html"
    build_run_container tar zcvf /wd/results/gpf-html.tar.gz -C _build/ html/

  }

  build_stage "Publish documentation"
  {

    local branch=$(e gpf_documentation_git_branch)

    if [ "$branch" == "master" ]; then
        local iossifovlab_infra_ref;
        iossifovlab_infra_ref=$(e docker_img_iossifovlab_infra)

        build_run_ctx_init "container" "${iossifovlab_infra_ref}"
        defer_ret build_run_ctx_reset

        # copy host's .ssh dir as the root .ssh in the container
        build_run_container_cp_to /root/ $HOME/.ssh
        build_run_container chown -R root:root /root/.ssh

        build_run_container bash -c "
            /opt/conda/bin/conda run --no-capture-output -n infra \
            ansible-playbook -i doc_inventory doc_publish.yml"
    else
        build_run_local echo "Skip publish documentation because the branch is not master"
    fi

  }

}

main "$@"
