#!/bin/sh

docker-compose -f docker-compose.yml down

git clean -xdf -e data-hg19-startup.tar.gz data-hg19-startup-latest.tar.gz data-hg19-startup
