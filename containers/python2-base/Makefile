all: build_container

build_container:
	cp ../../*-environment.yml .
	docker build . -f Dockerfile -t seqpipe/python2-base
	rm *-environment.yml

clean:
	docker rmi seqpipe/python2-base
