#!/bin/bash

set -e

mysql -u root -psecret -h mysql \
    -e "CREATE DATABASE IF NOT EXISTS test_gpf" 

mysql -u root -psecret -h mysql \
    -e "GRANT ALL PRIVILEGES ON test_gpf.* TO 'seqpipe'@'%' IDENTIFIED BY 'secret' WITH GRANT OPTION"
