FROM seqpipe/seqpipe-anaconda-base:latest

ARG SOURCE_DIR="."


ADD ${SOURCE_DIR}/conda-environment.yml /

RUN /opt/conda/bin/conda create \
    -c defaults -c conda-forge -c iossifovlab -c bioconda \
    --name gpf --file /conda-environment.yml
# RUN echo "conda activate gpf" >> ~/.bashrc

# GPF ENV
ENV PATH /opt/conda/envs/gpf/bin:$PATH

# HADOOP CONFIG
ENV JAVA_HOME /opt/conda/envs/gpf
ENV HADOOP_HOME /opt/conda/envs/gpf
ENV HADOOP_CONF_DIR /opt/conda/envs/gpf/etc/hadoop

RUN /opt/conda/envs/gpf/bin/pip install flake8-html

RUN mkdir -p /data && mkdir -p /code


ENV DAE_DB_DIR "/data"

WORKDIR /code

SHELL ["/bin/bash", "-c"]
