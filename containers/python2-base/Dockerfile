FROM continuumio/miniconda

COPY python2-environment.yml /

RUN apt-get update --fix-missing && \ 
	apt-get install -y default-libmysqlclient-dev gcc && \
	apt-get clean

RUN conda update -n base conda && \
	conda clean --all -y

RUN conda env update -f python2-environment.yml --verbose && \
	conda clean --all -y && \
	rm -r ~/.cache/pip

# remove an old libstdc++ from conda
RUN rm /opt/conda/lib/libstdc++.so.6.0.19

COPY . /code

WORKDIR /code
