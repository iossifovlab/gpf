ARG GPF_DOCKER_IMAGE

FROM $GPF_DOCKER_IMAGE

ENV DAE_SOURCE_DIR="/documentation/userdocs/gpf"

ENV DOCUMENTATION_DIR="/documentation"

WORKDIR /documentation
