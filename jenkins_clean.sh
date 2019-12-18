#!/bin/sh

docker-compose -f docker-compose.yml down


docker run busybox \
    -v ${SOURCE_DIR}:/code \
    /bin/sh -c "rm -rf /code/wdae-*.log && rm -rf /code/wdae_django*.cache"
