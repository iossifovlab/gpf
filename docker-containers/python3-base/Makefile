all: build_container

build_container:
	docker build ../.. -f Dockerfile -t seqpipe/python3-base

clean:
	docker rmi seqpipe/python3-base
