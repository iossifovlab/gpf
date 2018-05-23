#!/usr/bin/env bash

conda install \
	pytest \
	future \
	numpy \
	pysam \
	configparser \
	pandas \
	enum34 \
	sqlalchemy \
	scipy \
	statsmodels \
	matplotlib \
	seaborn \
	mysql-python \
	pytest-mock

pip install \
	reusables \
	python-box \
	Django==1.10 \
	djangorestframework \
	django-guardian \
	django-cors-headers \
	pytest-django
