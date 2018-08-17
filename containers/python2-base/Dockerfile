FROM continuumio/miniconda

RUN mkdir /data-work && mkdir /spark-home && mkdir /data-raw-dev

RUN apt-get update --fix-missing && \ 
	apt-get install -y default-libmysqlclient-dev gcc libgl1-mesa-glx openjdk-8-jre-headless && \
	apt-get clean

COPY python2-environment.yml /

RUN conda env update -n root -f python2-environment.yml && \
	conda clean --all -y && \
	# FIXME: should setup env with local versions somewhere else
	pip install git+git://github.com/seqpipe/cyvcf2 && \
	rm -r ~/.cache/pip

COPY . /code

WORKDIR /code

ENV DAE_SOURCE_DIR="/code/DAE"
ENV DAE_DB_DIR="/data-work"
ENV PYTHONPATH="$DAE_SOURCE_DIR:$PYTHONPATH"

ENV SPARK_HOME="/spark-home"
ENV THRIFTSERVER_PORT="60008"

ENV DAE_DATA_DIR="/data-raw-dev"
ENV DATA_DATASETS_DIR="/data-raw-dev/datasets"
ENV DAE_CONFIG_FILE="variants.conf"

SHELL ["/bin/bash", "-c"]
