#!/usr/bin/env bash

conda install \
	pytest \
	future \
	numpy \
	pandas \
	sqlalchemy \
	scipy \
	statsmodels \
	matplotlib \
	seaborn \
	pytest-mock \
	pytest-cov

pip install \
	pysam \
	mysqlclient \
	reusables \
	python-box \
	Django==1.10 \
	djangorestframework \
	django-guardian \
	django-cors-headers \
	pytest-django
