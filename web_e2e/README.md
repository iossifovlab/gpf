## Run e2e instance

Activate your `gpf` conda environment (make sure your packages are up to date with pip install):

```bash
conda activate gpf
```

Source the `setenv.sh` file in the `gpf-e2e` directory:

```bash
source ./setenv.sh
```

Import data: 

```bash
./gpf_e2e_instance/import_data.sh
```

Apply django migrations, create users and Oauth application:

```bash
wdaemanage.py migrate
./scripts/wdae_create_dev_users.sh
./scripts/wdae_create_local_dev_gpfjs_app.sh
```

Run Django development server:

```bash
wdaemanage.py runserver
```

Run Angular development server from `gpfjs` directory: 

```bash
ng serve
```

The e2e instance can now be browsed at `http://localhost:4200/`

## Run tests

In the gpf-e2e dir

Install packages:

```
sudo rm -rf node_modules
npm install
```

Setup mailhog:

```bash
docker compose up --detach
```

Edit `gpf-e2e/playwright/tests/utils.ts`:
Replace:
```ts
export const frontendUrl = 'http://gpf:8080/gpf';
export const backendUrl = frontendUrl;
export const mailhogUrl = 'http://mailhog:8025';
```

with:
```ts
export const backendUrl = 'http://localhost:8000';
export const frontendUrl = 'http://localhost:4200';
export const mailhogUrl = 'http://localhost:8025';
```

Edit `gpf-e2e/playwright.config.ts`:
Replace:
```bash
workers: process.env.CI ? undefined : undefined,
```

with:
```bash
workers: process.env.CI ? 1 : 1,

```

Run tests in terminal:

```
npx playwright test
```

Run tests using playwright's UI:

```
npx playwright test --ui
```

Run a specific spec:

```
npx playwright test -g <spec name>
```


## Run e2e instance in docker containers
(This workflow is used on Jenkins. Do this only if you debug Jenkins/docker specific issue)

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


## Run local gpfjs on docker container gpf

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
