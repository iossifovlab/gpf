ARG REGISTRY=""
ARG BASE_IMAGE_TAG=latest
FROM ${REGISTRY}gpf-dev:${BASE_IMAGE_TAG}

ARG SOURCE_DIR="."

ADD ${SOURCE_DIR}/impala2-environment.yml /

RUN /opt/conda/bin/mamba env update --name gpf --file /impala2-environment.yml
