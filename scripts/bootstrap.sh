#!/usr/bin/env bash

sudo apt update && \
    apt dist-upgrade -y && \
    apt install -y python-dev libmysqlclient-dev build-essential


wget -c https://repo.continuum.io/archive/Anaconda2-4.4.0-Linux-x86_64.sh

bash Anaconda2-4.4.0-Linux-x86_64.sh -b -p /home/ubuntu/anaconda2

chown ubuntu:ubuntu -R /home/ubuntu/anaconda2


export PATH=/home/ubuntu/anaconda2/bin:$PATH

conda env update -f /vagrant/root-anaconda-environment.yml

pip install mysqlclient==1.3.7

cat >> /home/ubuntu/.profile < /vagrant/scripts/vagrant-profile.template
