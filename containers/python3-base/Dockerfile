FROM continuumio/miniconda3

RUN mkdir /data && mkdir /spark-home && mkdir /code

RUN apt-get update --fix-missing && \ 
	apt-get install -y build-essential default-libmysqlclient-dev gcc libgl1-mesa-glx openjdk-8-jre-headless procps vim libsasl2-dev && \
	apt-get clean

COPY python3-environment.yml /code

RUN conda env update -n base -f /code/python3-environment.yml && \
    conda install -c conda-forge pyarrow=0.13.0 && \
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
