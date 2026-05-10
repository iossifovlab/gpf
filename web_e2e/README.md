# gpf web_e2e — Playwright suite

End-to-end tests for the GPF web stack. Two ways to run them:

- **Local dev** — fastest cycle. Run the backend with `wdaemanage runserver`, the frontend with `ng serve`, and Playwright against `http://127.0.0.1:8080/gpf`. This is what you want day-to-day.
- **Jenkins-mirrored compose stack** — runs the same images CI runs, against the same `web_infra/compose-jenkins.yaml`. Use this only when reproducing a Jenkins-only failure.

This README walks through both. For a snapshot of currently-failing tests and the cluster-level reasoning behind the CI configuration choices (capped Playwright workers, OAuth seeding), see [`../../issues/test-failures-summary.md`](../../issues/test-failures-summary.md) in the meta-repo.

---

## Local-dev workflow

### Prerequisites (one-time)

```bash
# 1. Activate the gpf conda env (created per the top-level gpf README)
conda activate gpf

# 2. Make sure gpf-core, gpf-web, and gain are editable-installed
pip install -e ../gain/core
pip install -e core
pip install -e web

# 3. Install the SPA's npm deps (web_ui is the gpfjs source)
cd web_ui && npm install && cd ..

# 4. Install Playwright + browsers (one-off, ~500 MB)
cd web_e2e
npm install
npx playwright install --with-deps chromium
cd ..
```

### Bring the data up (once per checkout, or after a schema change)

`import_data.sh` is **self-contained**: it migrates the Django DB, imports genotypes/phenotypes into `web_e2e/gpf_e2e_instance/`, generates common reports & gene profiles, seeds the dev users (`admin@iossifovlab.com` etc., password `secret`), and registers the OAuth `gpfjs` application. Re-running it is idempotent for the user and OAuth steps; the genotype/phenotype imports clean and rebuild from scratch.

```bash
# from the gpf checkout root
export DAE_DB_DIR="$PWD/web_e2e/gpf_e2e_instance"
export DJANGO_SETTINGS_MODULE=gpf_web.settings  # or wgpf_settings; see below
./web_e2e/gpf_e2e_instance/import_data.sh
```

The script's `wdaemanage createapplication` call uses redirect URIs that include `http://localhost:4200/login` and `http://127.0.0.1:8080/gpf/login`, so both dev-server topologies (Angular CLI on 4200 against Django on 8000, **or** `wgpf` on 8080) authenticate out of the box.

`import_data.sh` reads from whatever GRR your shell has configured. CI uses both `grr` and `grr_sfari` (combined as a group via `gpf_e2e_instance/grr-definition.yaml` — see the Jenkins-mirrored compose section below); local-dev uses your machine's default GRR. Once test fixtures start referencing `grr_sfari`-only resources, your local GRR will need both repos available too — point `GRR_DEFINITION_FILE` at `gpf_e2e_instance/grr-definition.yaml` (adjusting the `directory:` paths to your local layout) or roll your own definition with the same children.

### Run the dev servers

Open two terminals:

```bash
# Terminal 1 — Django backend on :8000
conda activate gpf
export DAE_DB_DIR="$PWD/web_e2e/gpf_e2e_instance"
wdaemanage runserver
```

```bash
# Terminal 2 — Angular SPA on :4200, proxied to backend at :8000
cd web_ui
ng serve
```

Browse the instance at <http://localhost:4200/>. Log in as `admin@iossifovlab.com` / `secret`.

### Run the Playwright suite

`web_e2e/tests/utils.ts` and `web_e2e/playwright.config.ts` automatically switch URLs based on `process.env.JENKINS`:

| Env                | `frontendUrl` / `baseURL`              | Used by                         |
| ------------------ | -------------------------------------- | ------------------------------- |
| no env vars        | `http://127.0.0.1:8080/gpf`            | local `wgpf`-style deploy       |
| `JENKINS=1`        | `http://frontend`                      | the compose stack (CI)          |

If you're running the dev-server topology (`ng serve` on 4200 + `wdaemanage runserver` on 8000), point Playwright at the SPA dev server with the local-dev override block already commented in `tests/utils.ts`:

```ts
// web_e2e/tests/utils.ts — uncomment for ng-serve / runserver
// export const frontendUrl = 'http://localhost:4200';
// export const backendUrl  = 'http://localhost:8000';
// export const mailhogUrl  = 'http://localhost:8025';
```

Don't commit that swap — leave the production `http://frontend` URLs as the default for CI. Then:

```bash
cd web_e2e

# headless run, default reporter
npx playwright test

# UI mode (most useful for writing/debugging a single spec)
npx playwright test --ui

# one spec by file
npx playwright test tests/datasets.spec.ts

# match a test name with -g
npx playwright test -g "should display \"GPF"

# slow it down + open the inspector at the first failing line
PWDEBUG=1 npx playwright test tests/datasets.spec.ts
```

### Mailhog (for the user-creation / forgotten-password specs)

The verification-email tests poll Mailhog for a message containing the freshly-created user's email and follow the link inside. For local dev:

```bash
# in another terminal
docker run --rm -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

Or use the `mail` service from `web_infra/compose-jenkins.yaml` if you're already running that stack. Either way, point Django at it via env:

```bash
export WDAE_EMAIL_HOST=localhost
export WDAE_EMAIL_PORT=1025
export WDAE_EMAIL_VERIFICATION_ENDPOINT=http://localhost:4200
```

---

## Jenkins-mirrored compose stack

Use this only when you're reproducing a CI-only failure. It runs the same images Jenkins builds (`gpf-web-api-prod` + `gpf-web-ui-prod`), wires them via `web_infra/compose-jenkins.yaml`, and fires the Playwright suite from the `e2e-tests` service.

The compose stack bind-mounts two GRR repos from the CSHL Jenkins agents — `/mnt/cephfs/seqpipe/grr` and `/mnt/cephfs/seqpipe/grr_sfari` — and points `GRR_DEFINITION_FILE` at `gpf_e2e_instance/grr-definition.yaml`, which combines them as a `group` repo (`grr_sfari` first, so its enrichment backgrounds override matching IDs in `grr`). On a host without those mounts, either provide equivalent paths or override `GRR_DEFINITION_FILE` to a definition that uses your local layout.

### Build the prod images locally

CI pulls them from `registry.seqpipe.org`; locally we build from the repo wheels.

```bash
# from the gpf root
mkdir -p dist/core dist/web dist/gain

# 1. gain-core wheel (gpf-core depends on it)
cd ../gain && uv build --package gain-core --out-dir ../gpf/dist/gain && cd ../gpf

# 2. gpf-core + gpf-web wheels
uv build --package gpf-core --out-dir dist/core
uv build --package gpf-web  --out-dir dist/web

# 3. backend image (Django + gunicorn)
docker build -f web/Dockerfile.production    -t gpf-web-api-prod:local .

# 4. frontend image (Angular SPA + Apache reverse-proxy)
docker build -f web_ui/Dockerfile.production \
    --build-arg BACKEND_IMAGE=gpf-web-api-prod:local \
    -t gpf-web-ui-prod:local .
```

### Bring the stack up

```bash
export BACKEND_IMAGE=gpf-web-api-prod:local
export FRONTEND_IMAGE=gpf-web-ui-prod:local
export COMPOSE_PROJECT=gpf-web-e2e-local

# 1. Run instance-import to its completion
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml \
    up -d db instance-import
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml \
    wait instance-import
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml \
    logs --no-color instance-import

# 2. Bring up backend + frontend explicitly (mirrors Jenkinsfile.e2e —
#    explicit up so step 3's --no-deps doesn't trigger a re-import)
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml \
    up -d mail backend-e2e frontend-e2e

# 3. Run the suite
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml \
    run --rm --no-deps e2e-tests
```

### Iterate on a subset

```bash
# Single spec
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml \
    run --rm --no-deps e2e-tests \
    npx playwright test --reporter=list tests/datasets.spec.ts

# Single test by name
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml \
    run --rm --no-deps e2e-tests \
    npx playwright test --reporter=list -g "should display \"GPF"

# Sanity-check the API from inside the network
docker run --rm --network "${COMPOSE_PROJECT}_default" curlimages/curl:latest \
    sh -c 'curl -fsS http://frontend/api/v3/instance/version && echo'
```

### Tear down

```bash
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml \
    down -v --remove-orphans
```

`-v` removes the named MariaDB volume; on next start `instance-import` re-runs from a clean DB.

### What's special about the compose stack

A few things differ from a vanilla `wdaemanage runserver` setup. They're load-bearing:

- **Apache (frontend) reverse-proxies `/api/`, `/ws/`, `/o/`, `/accounts/`** to the backend on port 9001. The SPA fallback `RewriteRule` excludes those prefixes so they don't get rewritten to `index.html`.
- **`/o/` and `/accounts/` are required for OAuth.** The SPA's log-in button does `window.location = /o/authorize/?...`, which the backend redirects to `/accounts/login/`. Both must be proxied.
- **Playwright workers are capped at 4 in CI** (`playwright.config.ts`). Local-dev (without `CI=1`) keeps Playwright's default.
- **`WDAE_EMAIL_VERIFICATION_ENDPOINT=http://frontend`.** Django bakes this URL into outbound mail; without it, the user-creation specs follow a `localhost:8000` link that chromium inside the network can't reach.
- **Backend logs are captured to `web_infra/wdae-logs/`.** Both `instance-import` and `backend-e2e` mount `./wdae-logs:/logs` and run with `WDAE_LOG_DIR=/logs`, so Django's `WatchedFileHandler` writes `wdae-debug.log` to a host bind that survives `compose down -v`. CI archives it (along with a wide combined `reports/web_e2e/compose.log` from `compose logs --no-color`) under the build's artefacts.

---

## Triaging a failure

1. Look up the spec in [`../../issues/test-failures-summary.md`](../../issues/test-failures-summary.md). Most of the currently-failing specs are listed with hypotheses and reproduction commands.
2. If it's not there, run it standalone with `--reporter=list` and Playwright's trace:
   ```bash
   PLAYWRIGHT_HTML_REPORT=playwright-report \
   npx playwright test --trace=on tests/foo.spec.ts -g "name"
   npx playwright show-report playwright-report
   npx playwright show-trace test-results/.../trace.zip
   ```
3. For backend errors, either dump per-service logs from the running compose stack
   ```bash
   docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml \
       logs --no-color backend-e2e --tail 200
   ```
   or, on a CI build, grab the `wdae-debug.log` and `compose.log` artefacts archived by the Jenkins job — `wdae-debug.log` has the per-request Django output, `compose.log` interleaves every service's stdout by timestamp.
4. File a new issue: `gh issue create --repo iossifovlab/gpf --label needs-triage`. The umbrella `genomics-toolbox/CLAUDE.md` documents the label vocabulary and the workflow loop.
