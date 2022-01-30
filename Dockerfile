ARG REGISTRY=""
ARG BASE_IMAGE_TAG=latest
FROM ${REGISTRY}seqpipe-anaconda-base:${BASE_IMAGE_TAG}

ARG SOURCE_DIR="."


ADD ${SOURCE_DIR}/environment.yml /
ADD ${SOURCE_DIR}/dev-environment.yml /

RUN /opt/conda/bin/mamba env create --name gpf --file /environment.yml
RUN /opt/conda/bin/mamba env update --name gpf --file /dev-environment.yml

# http range server for testing
RUN /opt/conda/bin/conda run --no-capture-output -n gpf pip install rangehttpserver==1.2.0

# RUN echo "conda activate gpf" >> ~/.bashrc

# GPF ENV
ENV PATH /opt/conda/envs/gpf/bin:$PATH

# HADOOP CONFIG
ENV JAVA_HOME /opt/conda/envs/gpf
ENV HADOOP_HOME /opt/conda/envs/gpf
ENV HADOOP_CONF_DIR /opt/conda/envs/gpf/etc/hadoop

RUN mkdir -p /data && mkdir -p /code

ENV DAE_DB_DIR "/data"

WORKDIR /code

SHELL ["/bin/bash", "-c"]
