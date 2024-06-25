## Setup GPF e2e tests

Clear the previous e2e test instance:

```
./build_cleanup.sh
```

Setup a fresh one:

```
./build_setup.sh
```

After completion, the instance can be browsed at:

```
http://localhost:8080/gpf
```

## Run GPF e2e tests

```
sudo rm -rf node_modules
sudo rm -rf reports_new

npm install
```

To run tests in terminal:

```
npx playwright test
```

To run tests using playwright's UI:

```
npx playwright test --ui
```

To run a specific spec:

```
npx playwright test -g <spec name>
```

## Run GPF e2e instance on live GPFJS ng serve

Change `gpfjs/src/environments/environment.ts` line:

```
const basePath = 'http://localhost:8000';
```

to:

```
const basePath = 'http://<instance ip>:9001;
```

To get <instance ip>:

Inspect the IP address on which GPF system is accessible. To this end run

```
docker ps --filter label="build-scripts=local"
```

The output of this command should look like the following:

```
CONTAINER ID   IMAGE                                                      COMMAND                  CREATED...   STA...
0352bc66baa5   registry.seqpipe.org/seqpipe-gpf-full:master_57c04e5-664   "supervisord -c /etc…"   45 minu...   Up ...
f9fa020327e8   seqpipe/seqpipe-docker-impala:latest                       "supervisord -c /etc…"   49 minu...   Up ...
b7856fa20651   mysql:5.7                                                  "docker-entrypoint.s…"   49 minu...   Up ...
```

Find the container ID that corresponds to `registry.seqpipe.org/seqpipe-gpf-full` image.
In the above mentioned case this is the container with ID `0352bc66baa5`.

Run following command to inspect IP address of this container:

```
docker inspect \
    --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
    0352bc66baa5
```
