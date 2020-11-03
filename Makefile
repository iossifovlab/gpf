


all:

ifndef GPF_DOCKER_IMAGE
GPF_DOCKER_IMAGE="iossifovlab/gpf-base:documentation_master"
endif

ifndef DOCUMENTATION_DOCKER_IMAGE
DOCUMENTATION_DOCKER_IMAGE="seqpipe/gpf-documetation:master"
endif

ifndef WD
WD=$(shell pwd)
endif


gpf_image:
	echo $(GPF_DOCKER_IMAGE)
	docker build . -t $(GPF_DOCKER_IMAGE) -f "gpf/Dockerfile" --build-arg SOURCE_DIR=./gpf


documentation_image:
	echo $(DOCUMENTATION_DOCKER_IMAGE)
	docker build . -t $(DOCUMENTATION_DOCKER_IMAGE) -f ./Dockerfile --build-arg GPF_DOCKER_IMAGE=$(GPF_DOCKER_IMAGE)

documentation_build:
	docker run --rm \
	-v $(WD):/documentation \
	-v $(WD)/gpf:/documentation/userdocs/gpf \
	-v $(DAE_DB_DIR):/data \
	$(DOCUMENTATION_DOCKER_IMAGE) \
	/documentation/scripts/jenkins_build.sh
