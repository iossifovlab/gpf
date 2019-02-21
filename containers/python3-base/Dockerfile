FROM continuumio/miniconda3

RUN mkdir /data && mkdir /spark-home && mkdir /code

RUN apt-get update --fix-missing && \ 
	apt-get install -y default-libmysqlclient-dev gcc libgl1-mesa-glx openjdk-8-jre-headless procps vim && \
	apt-get clean

COPY python3-environment.yml /code

RUN conda env update -n root -f /code/python3-environment.yml && \
	conda clean --all -y && \
	# FIXME: should setup env with local versions somewhere else
	pip install git+git://github.com/seqpipe/cyvcf2 && \
	rm -r ~/.cache/pip

ENV DAE_SOURCE_DIR="/code/DAE"
ENV DAE_DB_DIR="/data"
ENV PYTHONPATH="$DAE_SOURCE_DIR:$PYTHONPATH"

ENV SPARK_HOME="/spark-home"
ENV THRIFTSERVER_PORT="60008"

ENV DAE_DATA_DIR="/data/parquet"

COPY . /code

WORKDIR /code

SHELL ["/bin/bash", "-c"]
