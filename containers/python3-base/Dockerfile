FROM continuumio/miniconda3

RUN mkdir /data-work

RUN apt-get update --fix-missing && \ 
	apt-get install -y default-libmysqlclient-dev gcc libgl1-mesa-glx && \
	apt-get clean

COPY python3-environment.yml /

RUN conda env update -n root -f python3-environment.yml && \
	conda clean --all -y && \
	rm -r ~/.cache/pip

COPY . /code

WORKDIR /code

ENV DAE_SOURCE_DIR="/code/DAE"
ENV DAE_DB_DIR="/data-work"
ENV PYTHONPATH="$DAE_SOURCE_DIR:$PYTHONPATH"

SHELL ["/bin/bash", "-c"]
