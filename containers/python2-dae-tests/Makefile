all: build_container

build_container:
	docker build . -t seqpipe/python2-dae-tests

clean:
	docker rmi seqpipe/python2-dae-tests
