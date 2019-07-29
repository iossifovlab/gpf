#!/bin/bash


# UBUNTU 18.04

apt-get update --fix-missing && \ 
	apt-get install -y build-essential default-libmysqlclient-dev gcc \
        libgl1-mesa-glx openjdk-8-jdk-headless procps vim libsasl2-dev wget \
        apt-transport-https ca-certificates curl software-properties-common && \
	apt-get clean

export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64


# DOCKER

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
apt update
apt install  -y docker-ce
usermod -aG docker vagrant

# HADOOP
export HADOOP_VER=3.0.2

wget --quiet http://it.apache.contactlab.it/hadoop/core/hadoop-${HADOOP_VER}/hadoop-${HADOOP_VER}.tar.gz
tar -xf hadoop-$HADOOP_VER.tar.gz -C ..; \
    mv ../hadoop-${HADOOP_VER} /opt/hadoop

export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

cp /vagrant/scripts/configs/vagrant/etc/core-site.xml ${HADOOP_CONF_DIR}/core-site.xml


# ANACONDA

wget --quiet https://repo.anaconda.com/archive/Anaconda3-2019.07-Linux-x86_64.sh -O /anaconda.sh && \
    /bin/bash /anaconda.sh -b -p /opt/conda && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/ && \
    rm /anaconda.sh

/opt/conda/bin/conda init bash

/opt/conda/bin/conda create -c conda-forge -c bioconda \
    --name gpf --file /vagrant/conda-environment.yml

# PIP
/opt/conda/envs/gpf/bin/pip install reusables

# cat <<EOT >> /etc/hosts

# 127.0.0.1       impala

# EOT

cat <<EOT >> /home/vagrant/.bashrc

export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

export DAE_SOURCE_DIR="/vagrant/DAE"
export DAE_DB_DIR="/data"

export DAE_GENOMIC_SCORES_HG19=/genomic-scores-hg19
export DAE_GENOMIC_SCORES_HG38=/genomic-scores-hg38

export HADOOP_HOME=/opt/hadoop

source /vagrant/scripts/setenv-vagrant.sh

EOT