FROM continuumio/miniconda3

COPY python3-environment.yml /

ENV DAE_SOURCE_DIR="/code/DAE"
ENV DAE_DB_DIR="/data-work"

RUN apt-get update --fix-missing && \ 
	apt-get install -y default-libmysqlclient-dev gcc && \
	apt-get clean

RUN conda update -n base conda && conda clean --all -y

RUN conda env update -f python3-environment.yml --verbose && \
	conda clean --all -y && \
	rm -r ~/.cache/pip

# remove an old libstdc++ from conda
RUN rm /opt/conda/lib/libstdc++.so.6.0.24

COPY . /code

WORKDIR /code
