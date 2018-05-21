all: build_container

build_container:
	docker build . -t seqpipe/python3-dae-tests

clean:
	docker rmi seqpipe/python3-dae-tests
