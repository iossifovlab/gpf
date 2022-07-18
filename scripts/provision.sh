#!/bin/bash


# UBUNTU 20.04

DEBIAN_FRONTEND=noninteractive apt-get update --fix-missing && \ 
	DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y && \
	DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential gcc wget git python-lxml \
        ca-certificates \
        curl \
        gnupg \
        lsb-release && \
	DEBIAN_FRONTEND=noninteractive apt-get clean


# DOCKER
sudo mkdir -p /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null 

DEBIAN_FRONTEND=noninteractive apt update
DEBIAN_FRONTEND=noninteractive apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

usermod -aG docker vagrant


# MINICONDA
mkdir -p /root/.conda/

wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh -O /miniconda.sh && \
    /bin/bash /miniconda.sh -b -p /opt/conda && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/ && \
    rm /miniconda.sh

/opt/conda/bin/conda init bash

export PATH=/opt/conda/bin:$PATH

conda install -c defaults -c conda-forge \
    python=3.9 mamba=0.24 \
    bump2version conda-build conda-pack boa anaconda-client

ln -s /opt/conda/lib/libarchive.so.18 /opt/conda/lib/libarchive.so.13

chown vagrant:vagrant -R /opt/conda

sudo -u vagrant /opt/conda/bin/conda init bash

sudo -u vagrant /opt/conda/bin/mamba env create --name gpf --file /vagrant/environment.yml
sudo -u vagrant /opt/conda/bin/mamba env update --name gpf --file /vagrant/dev-environment.yml

# cat <<EOT >> /home/vagrant/.bashrc


# EOT