FROM seqpipe/seqpipe-node-base:latest

ARG SOURCE_DIR="."


ADD ${SOURCE_DIR}/conda-environment.yml /

RUN /opt/conda/bin/conda create -c conda-forge -c bioconda -c iossifovlab \
    --name gpf --file /conda-environment.yml
RUN echo "conda activate gpf" >> ~/.bashrc

# GPF ENV
ENV PATH /opt/conda/envs/gpf/bin:/opt/conda/bin:$PATH

# HADOOP CONFIG
ENV JAVA_HOME /opt/conda/envs/gpf
ENV HADOOP_HOME /opt/conda/envs/gpf
ENV HADOOP_CONF_DIR /opt/conda/envs/gpf/etc/hadoop

RUN mkdir -p /data && mkdir -p /code


ENV DAE_DB_DIR="/data"


ENV DAE_IMPALA_HOST "impala"
ENV DAE_IMPALA_PORT 21050

WORKDIR /code

SHELL ["/bin/bash", "-c"]
