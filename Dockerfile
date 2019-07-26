FROM amd64/ubuntu:18.04

RUN apt-get update --fix-missing && \ 
	apt-get install -y build-essential default-libmysqlclient-dev gcc \
        libgl1-mesa-glx openjdk-8-jdk-headless procps vim libsasl2-dev \
        wget && \
	apt-get clean

# HADOOP
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64
ENV HADOOP_VER 3.0.2

RUN wget --quiet http://it.apache.contactlab.it/hadoop/core/hadoop-${HADOOP_VER}/hadoop-${HADOOP_VER}.tar.gz
RUN tar -xf hadoop-$HADOOP_VER.tar.gz -C ..; \
    mv ../hadoop-${HADOOP_VER} /opt/hadoop

ENV HADOOP_HOME /opt/hadoop
ENV HADOOP_CONF_DIR $HADOOP_HOME/etc/hadoop

ENV PATH $HADOOP_HOME/bin:$PATH
ENV LD_LIBRARY_PATH $HADOOP_HOME/lib/native/:$LD_LIBRARY_PATH

ADD ./docker-container/etc/core-site.xml ${HADOOP_CONF_DIR}/core-site.xml


# ANACONDA

RUN wget --quiet https://repo.anaconda.com/archive/Anaconda3-2019.07-Linux-x86_64.sh -O /anaconda.sh && \
    /bin/bash /anaconda.sh -b -p /opt/conda && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/ && \
    rm /anaconda.sh

RUN /opt/conda/bin/conda init bash

ADD ./conda-environment.yml /

RUN /opt/conda/bin/conda create -c conda-forge -c bioconda \
    --name gpf --file /conda-environment.yml
RUN echo "conda activate gpf" >> ~/.bashrc

# PIP
RUN /opt/conda/envs/gpf/bin/pip install reusables

RUN mkdir /data && mkdir /code


ENV DAE_SOURCE_DIR="/code/DAE"
ENV DAE_DB_DIR="/data"
ENV PYTHONPATH="$DAE_SOURCE_DIR:$PYTHONPATH"
ENV PATH /opt/conda/envs/gpf/bin:/opt/conda/bin:$PATH

ENV DAE_IMIPALA_HOST="impala"
ENV DAE_IMPALA_PORT=21050

WORKDIR /code


SHELL ["/bin/bash", "-c"]
