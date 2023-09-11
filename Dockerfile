FROM --platform=linux/amd64 condaforge/mambaforge:latest


ADD environment.yml /
ADD dev-environment.yml /

RUN /opt/conda/bin/mamba env create --name gpf --file /environment.yml
# RUN /opt/conda/bin/mamba env update --name gpf --file /dev-environment.yml


# GPF ENV
ENV PATH /opt/conda/envs/gpf/bin:$PATH

RUN mkdir -p /data && mkdir -p /code

ENV DAE_DB_DIR "/data"

WORKDIR /code

SHELL ["/bin/bash", "-c"]
