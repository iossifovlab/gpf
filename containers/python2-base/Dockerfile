FROM continuumio/miniconda

ENV DAE_SOURCE_DIR="/code/DAE"
ENV DAE_DB_DIR="/data-work"

RUN mkdir /data-work

RUN apt-get update --fix-missing && \ 
	apt-get install -y default-libmysqlclient-dev gcc libgl1-mesa-glx && \
	apt-get clean

#RUN conda update -n base conda && \
#	conda clean --all -y

COPY python2-environment.yml /

RUN conda env update -f python2-environment.yml --verbose && \
	conda clean --all -y && \
	rm -r ~/.cache/pip

# remove an old libstdc++ from conda
#RUN rm /opt/conda/lib/libstdc++.so.6.0.19

COPY . /code

WORKDIR /code
