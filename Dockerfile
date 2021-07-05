FROM seqpipe/seqpipe-anaconda-base:latest

ARG SOURCE_DIR="."


ADD ${SOURCE_DIR}/environment.yml /
ADD ${SOURCE_DIR}/dev-environment.yml /

RUN /opt/conda/bin/conda env create --name gpf --file /environment.yml
RUN /opt/conda/bin/conda env update --name gpf --file /dev-environment.yml --prune
# RUN echo "conda activate gpf" >> ~/.bashrc

RUN conda install -n gpf -c defaults -c conda-forge gunicorn mysqlclient
RUN conda install -n gpf -c defaults -c conda-forge -c anaconda mysql-connector-python

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
