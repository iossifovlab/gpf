#!/bin/sh

docker-compose -f docker-compose.yml down

git clean -xdf -e data-hg19-startup.tar.gz -e data-hg19-startup-latest.tar.gz -e data-hg19-startup
