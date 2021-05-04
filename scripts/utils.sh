#!/usr/bin/env bash


function create_docker_network {

    if [ -z $JENKINS ];
    then
        DOCKER_NETWORK_ARG=""
    else
        HAS_NETWORK=`docker network ls | grep ${NETWORK} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`

        if [[ -z $HAS_NETWORK ]]; then
            echo "going to create docker network ${NETWORK}"
            docker network create -d bridge ${NETWORK} || true
        fi
        DOCKER_NETWORK_ARG="--rm --network ${NETWORK}"
    fi
    echo "docker network to use: ${DOCKER_NETWORK_ARG}"
}


function run_gpf_impala {

    create_docker_network
    if [ -z $JENKINS ];
    then
        DOCKER_GPF_IMPALA_PORT_ARG="-p 8020:8020 -p 9870:9870 -p 9864:9864 -p 21050:21050 -p 25000:25000 -p 25010:25010 -p 25020:25020"
    else
        DOCKER_GPF_IMPALA_PORT_ARG=""
    fi

    echo "Looking for gpf impala container: ${CONTAINER_GPF_IMPALA}"
    export HAS_GPF_RUNNING_IMPALA=`docker ps | grep ${CONTAINER_GPF_IMPALA} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
    export HAS_GPF_IMPALA=`docker ps -a | grep ${CONTAINER_GPF_IMPALA} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
    if [[ -z $HAS_GPF_RUNNING_IMPALA ]]; then
        # create gpf_impala docker container

        if [[ -z $HAS_GPF_IMPALA ]];
        then
            echo "going to create gpf impala container ${CONTAINER_GPF_IMPALA}"
            docker pull seqpipe/seqpipe-docker-impala:latest
            docker run -d ${DOCKER_NETWORK_ARG} \
                --name ${CONTAINER_GPF_IMPALA} \
                --hostname impala ${DOCKER_GPF_IMPALA_PORT_ARG} \
                seqpipe/seqpipe-docker-impala:latest
        else
            docker start ${CONTAINER_GPF_IMPALA}
        fi
    fi

    echo "waiting gpf_impala container..."
    docker exec ${CONTAINER_GPF_IMPALA} /wait-for-it.sh -h localhost -p 21050 -t 300

}


function run_mysql {

    create_docker_network
    if [ -z $JENKINS ];
    then
        DOCKER_GPF_MYSQL_PORT_ARG="-p 3306:3306"
    else
        DOCKER_GPF_MYSQL_PORT_ARG=""
    fi

    export HAS_RUNNING_GPF_MYSQL=`docker ps | grep ${CONTAINER_GPF_MYSQL} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
    export HAS_GPF_MYSQL=`docker ps -a | grep ${CONTAINER_GPF_MYSQL} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`

    if [[ -z $HAS_RUNNING_GPF_MYSQL ]]; then

        if [[ -z $HAS_GPF_MYSQL ]]; then
            # create gpf_impala docker container

            docker pull mysql:5.7

            docker run -d ${DOCKER_NETWORK_ARG} \
                --name ${CONTAINER_GPF_MYSQL} \
                --hostname mysql ${DOCKER_GPF_MYSQL_PORT_ARG} \
                -e "MYSQL_DATABASE=gpf" \
                -e "MYSQL_USER=seqpipe" \
                -e "MYSQL_PASSWORD=secret" \
                -e "MYSQL_ROOT_PASSWORD=secret" \
                -e "MYSQL_PORT=3306" \
                mysql:5.7 \
                --character-set-server=utf8 --collation-server=utf8_bin

        else
            docker start ${CONTAINER_GPF_MYSQL}
        fi

        echo "Going to wait for MySQL container ${CONTAINER_GPF_MYSQL} to be ready..."
        docker run \
            -d ${DOCKER_NETWORK_ARG} \
            --link ${CONTAINER_GPF_MYSQL}:mysql \
            --entrypoint /bin/bash \
            ${IMAGE_GPF_DEV} -c "/code/scripts/wait-for-it.sh -h mysql -p 3306 -t 300"

        sleep 5

        docker run \
            -d ${DOCKER_NETWORK_ARG} \
            --link ${CONTAINER_GPF_MYSQL}:mysql \
            --entrypoint /bin/bash \
            ${IMAGE_GPF_DEV} -c "/code/scripts/internal_run_mysql.sh"

    fi

}

function run_gpf_remote {
    if [ -z $JENKINS ];
    then
        DOCKER_GPF_REMOTE_PORT_ARG="-p 21010:21010"
    else
        DOCKER_GPF_REMOTE_PORT_ARG=""
    fi

    echo "Looking for gpf remote container: ${CONTAINER_GPF_REMOTE}"
    export HAS_RUNNING_GPF_REMOTE=`docker ps | grep ${CONTAINER_GPF_REMOTE} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
    export HAS_GPF_REMOTE=`docker ps -a | grep ${CONTAINER_GPF_REMOTE} | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`

    if [[ -z $HAS_RUNNING_GPF_REMOTE ]];
    then

        if [[ -z $HAS_GPF_REMOTE ]];
        then
            echo "Going to create GPF remote container ${CONTAINER_GPF_REMOTE}..."
            docker run \
                -d ${DOCKER_NETWORK_ARG} \
                --link ${CONTAINER_GPF_IMPALA}:impala \
                --entrypoint /bin/bash \
                --name ${CONTAINER_GPF_REMOTE} \
                --hostname gpfremote ${DOCKER_GPF_REMOTE_PORT_ARG} \
                -v ${WD}:/code \
                -v ${DAE_DB_DIR_REMOTE}:/data \
                -v ${IMPORT}:/import \
                -v ${DOWNLOADS}:/downloads \
                -v ${SCRIPTS}:/scripts \
                -e BUILD_NUMBER=${BUILD_NUMBER} \
                -e BRANCH_NAME=${BRANCH_NAME} \
                -e GPF_VERSION=${GPF_VERSION} \
                -e GPF_TAG=${GPF_TAG} \
                -e WORKSPACE="/" \
                -e WD="/" \
                -e DAE_DB_DIR="/data" \
                -e TEST_REMOTE_HOST=${CONTAINER_GPF_REMOTE} \
                -e MYSQL_DB_HOST="mysql" \
                ${IMAGE_GPF_DEV} -c "/opt/conda/bin/conda run --no-capture-output -n gpf /scripts/internal_run_gpf_remote.sh"
        else
            docker start ${CONTAINER_GPF_REMOTE}
        fi

        echo "Going to wait for GPF remote container ${CONTAINER_GPF_REMOTE} to be ready..."
        docker exec ${CONTAINER_GPF_REMOTE} /code/scripts/wait-for-it.sh -h localhost -p 21010 -t 300
    else
        echo "GPF remote container already running: ${CONTAINER_GPF_REMOTE}; nothing to do..."
    fi

}

export -f create_docker_network
export -f run_mysql
export -f run_gpf_impala
export -f run_gpf_remote
