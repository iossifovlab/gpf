all: build_container

build_container:
	docker build ../.. -f Dockerfile -t seqpipe/python2-base

clean:
	docker rmi seqpipe/python2-base
