
## Preliminary


### Add hosts record for registry.seqpipe.org


Add to `/etc/hosts`
```
10.0.1.7        registry.seqpipe.org
```

Check the name is resolved:
```
ping registry.seqpipe.org
```


Update `/etc/docker/daemon.json` to include:

```
{
    "insecure-registries" : ["registry.seqpipe.org:5000"]
}
```

and restart the docker deamon:

```
systemctl restart docker
```

and check that you have access to the seqpipe's docker registry:

```
docker pull registry.seqpipe.org:5000/seqpipe-gpf-full:latest
```

## Setup GPF e2e tests

Clear the previous e2e test instance:

```
./test_cleanup.sh
```

Setup a fresh one:

```
./tests_setup.sh
```

Instpect the IP address on whick GPF system is accessible:

```
docker inspect \
    --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
    gpf-e2e-dev-latest-genotype-impala-0
```

## Run GPF e2e tests


```
sudo rm -rf node_modules
sudo rm -rf reports_new

npm install .
```

```
./node_modules/.bin/cypress open --config baseUrl=http://<instance ip>/gpf/
```

where `<instance ip>` is the IP address reported from `docker inspect` command.

## Run GPF e2e tests with live GPFJS ng serve


Change `gpfjs/src/environments/environment.ts` line:

```
const basePath = 'http://localhost:8000';
```

to:

```
const basePath = 'http://<instance ip>:9001;
```
