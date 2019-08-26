FROM amd64/ubuntu:18.04

ARG SOURCE_DIR="."

RUN apt-get update --fix-missing && \ 
	apt-get install -y build-essential default-libmysqlclient-dev gcc \
        libgl1-mesa-glx procps vim libsasl2-dev \
        wget && \
	apt-get clean

# ANACONDA

RUN wget --quiet https://repo.anaconda.com/archive/Anaconda3-2019.07-Linux-x86_64.sh -O /anaconda.sh && \
    /bin/bash /anaconda.sh -b -p /opt/conda && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/ && \
    rm /anaconda.sh

RUN /opt/conda/bin/conda init bash

ADD ${SOURCE_DIR}/conda-environment.yml /

RUN /opt/conda/bin/conda create -c conda-forge -c bioconda -c iossifovlab \
    --name gpf --file /conda-environment.yml
RUN echo "conda activate gpf" >> ~/.bashrc

# HADOOP CONFIG
ENV HADOOP_HOME /opt/conda/envs/gpf
ENV HADOOP_CONF_DIR $HADOOP_HOME/etc/hadoop

# ENV PATH $HADOOP_HOME/bin:$PATH
# ENV LD_LIBRARY_PATH $HADOOP_HOME/lib/native/:$LD_LIBRARY_PATH

ADD ${SOURCE_DIR}//scripts/configs/docker-container/etc/core-site.xml ${HADOOP_CONF_DIR}/core-site.xml

# PIP

RUN mkdir /data && mkdir /code


ENV DAE_SOURCE_DIR="/code"
ENV DAE_DB_DIR="/data"
ENV PYTHONPATH="$DAE_SOURCE_DIR:$PYTHONPATH"
ENV PATH /opt/conda/envs/gpf/bin:/opt/conda/bin:$PATH

ENV DAE_IMPALA_HOST "impala"
ENV DAE_IMPALA_PORT 21050

WORKDIR /code

SHELL ["/bin/bash", "-c"]
