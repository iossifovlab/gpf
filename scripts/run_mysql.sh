#!/bin/bash
# Script intended for running mysql container with seqpipe user and gpf database

set -e


export HAS_GPF_MYSQL=`docker ps -a | grep gpf-mysql | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`


if [[ -z $HAS_GPF_MYSQL ]]; then
    # create gpf_impala docker container

    docker pull mysql:5.7

    docker create \
        --name gpf-mysql \
        --hostname gpf-mysql \
        -p 3306:3306 \
        -e "MYSQL_DATABASE=gpf" \
        -e "MYSQL_USER=seqpipe" \
        -e "MYSQL_PASSWORD=secret" \
        -e "MYSQL_ROOT_PASSWORD=secret" \
        -e "MYSQL_PORT=3306" \
        mysql:5.7 \
        --character-set-server=utf8 --collation-server=utf8_bin

fi

export HAS_RUNNING_GPF_MYSQL=`docker ps | grep gpf_mysql | sed -e "s/\s\{2,\}/\t/g" | cut -f 1`
echo "Has running GPF MySQL: <${HAS_RUNNING_GPF_MYSQL}>"
if [[ -z $HAS_RUNNING_GPF_MYSQL ]]; then
    echo "starting gpf_mysql container..."
    docker start gpf-mysql
fi

echo "waiting gpf_mysql container..."
./scripts/wait-for-it.sh -h 127.0.0.1 -p 3306 -t 300

sleep 5

echo ""
echo "==============================================="
echo "Local GPF MySQL is READY..."
echo "==============================================="
echo ""




mysql -u root -psecret -h 127.0.0.1 \
    -e "CREATE DATABASE IF NOT EXISTS test_gpf" 

sleep 2

mysql -u root -psecret -h 127.0.0.1 \
    -e "GRANT ALL PRIVILEGES ON test_gpf.* TO 'seqpipe'@'%' IDENTIFIED BY 'secret' WITH GRANT OPTION"
