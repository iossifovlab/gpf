#!/bin/bash
# Script intended for running mysql container with seqpipe user and gpf database

set -e


docker pull mysql:5.7

docker run -d -p 3306:3306 \
    -e "MYSQL_DATABASE=gpf" \
    -e "MYSQL_USER=seqpipe" \
    -e "MYSQL_PASSWORD=secret" \
    -e "MYSQL_ROOT_PASSWORD=secret" \
    -e "MYSQL_PORT=3306" \
    mysql:5.7 

