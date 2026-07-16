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

`import_data.sh` reads from whatever GRR your shell has configured. CI reads three node-local, materialized `type: directory` GRRs (`grr_sfari`, `grr`, `grr_seqpipe`) bind-mounted read-only, combined as a group via `gpf_e2e_instance/grr-definition.yaml` (see the Jenkins-mirrored compose section below); local-dev uses your machine's default GRR. Once test fixtures start referencing `grr_sfari`-only resources, your local GRR will need those repos available too — point `GRR_DEFINITION_FILE` at `gpf_e2e_instance/grr-definition.yaml` (its children point at `/grr_sfari`, `/grr`, `/grr_seqpipe`, which you must have checked out locally) or roll your own definition with the same children.

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
// export const mailpitUrl  = 'http://localhost:8025';
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

### Mailpit (for the user-creation / forgotten-password specs)

The verification-email tests poll Mailpit for a message containing the freshly-created user's email and follow the link inside. For local dev:

```bash
# in another terminal
docker run --rm -p 1025:1025 -p 8025:8025 mailpit/mailpit
```

Or use the `mail` service from `web_infra/compose-jenkins.yaml` if you're already running that stack. Either way, point Django at it via env:

```bash
export WDAE_EMAIL_HOST=localhost
export WDAE_EMAIL_PORT=1025
export WDAE_EMAIL_VERIFICATION_ENDPOINT=http://localhost:4200
```

---

## Jenkins-mirrored compose stack

Use this only when you're reproducing a CI-only failure. It runs the same images Jenkins builds, wires them via `web_infra/compose-jenkins.yaml` plus a stack-mode overlay, and fires the Playwright suite from the `e2e-tests` service.

There are two stack modes (matching the Jenkins job's `STACK_MODE` parameter):

- **`split`** — two HTTP services, `backend` (gunicorn) + `frontend` (Apache reverse-proxy). What the job has historically run.
- **`combined`** — one HTTP service, `frontend`, running the supervisord-managed `gpf-web-prod` image (gunicorn + Apache in one container — the artefact production currently ships).

Both overlays expose a service literally named `frontend`; the test suite's `http://frontend` baseURL works unchanged. Pick a mode by passing the matching overlay file alongside the shared base.

### The GRR: node-local `type: directory` trees, read-only

Every GRR-reading service (`instance-import`, split-mode `backend`, combined-mode `frontend`) points `GRR_DEFINITION_FILE` at `gpf_e2e_instance/grr-definition.yaml`, which is a `group` of three **node-local `type: directory`** repos that `grr-sync` materializes on the agent (atomic-publish mode, grr-sync#20; provisioned by seqpipe/infra#71):

| child id | directory | role |
|---|---|---|
| `grr_sfari.sync` | `/grr_sfari` | FIRST — enrichment-background overrides win |
| `grr.sync` | `/grr` | main GRR; same id `gain-web-e2e` uses |
| `grr_seqpipe.sync` | `/grr_seqpipe` | LAST — gap-filler (`coding_length_ref_gene_v20170601`) |

`grr_sfari` stays **first** — a group resolves an id from the first child that has it, and grr_sfari's enrichment backgrounds deliberately override the matching ids in `grr`. `grr_seqpipe` stays **last** so `grr`'s versions win any overlapping ids; it only fills the gap for `hg38/enrichment/coding_length_ref_gene_v20170601`, which the enrichment `selected_background_models` needs and which exists in no other repo. (This whole scheme replaces the earlier **http+cache** design — `grr{,-sfari}.seqpipe.org` behind a whole-file `/grr_cache` — and, before that, the dead `/mnt/cephfs/seqpipe/grr{,_sfari}` NFS bind-mounts; a bind-mount of a missing host path silently yields an *empty* directory.)

The compose files bind the three trees **read-only** from the grr-sync LVM root:

```yaml
- ${GRR_ROOT}/grr:/grr:ro
- ${GRR_ROOT}/grr_sfari:/grr_sfari:ro
- ${GRR_ROOT}/grr_seqpipe:/grr_seqpipe:ro
```

Consequences:

- **Don't rename the children.** grr-sync lays the node-local trees out by these repo ids; a rename points a child at a tree that isn't synced on the node. `grr.sync` is also what `gain-web-e2e` calls the main GRR, so on a shared agent both jobs read **one** node-local copy of it.
- **Reads are byte-range, off local disk.** A tabix/fasta/bigwig query reads only the bytes it needs — there is no cold-download tax and no cache to warm (the http+cache design forced whole-file materialization, ~32.5 GB worst case). The job's 4h timeout and the web-tier's 3600s `start_period` are now headroom for the import + gunicorn eager-loading, not a cold-GRR budget.
- **`:ro` means builds never write the shared tree.** grr-sync hardlinks resources across snapshots; a writable mount could corrupt a sibling snapshot.

In Jenkins, `GRR_ROOT` is set in the pipeline's `environment{}` block to the grr-sync LVM root (pin it to seqpipe/infra#71's actual mount path). Locally, set `GRR_ROOT` to a directory holding `grr/`, `grr_sfari/`, `grr_seqpipe/` checkouts.

`instance-import` and the split-mode `backend` still run as **`${AGENT_UID}:${AGENT_GID}`**, defaulting to `0:0` outside CI — **not** for the GRR (which is read-only) but because `instance-import` rewrites the checked-out instance dir *in the workspace*; running it as root would leave root-owned artifacts the next build's cleanup can't remove. `working_dir: /tmp` gives those CLIs a writable cwd for their `.task-log`. The combined-mode `frontend` stays root — the production image's supervisord declares `user=root` and refuses to start otherwise; harmless here since it only writes the two first-startup description files under `/data`.

#### GRR pre-flight, and the `.env` uid handshake

Before any container starts, `Jenkinsfile.e2e`'s **`Compose env`** stage asserts each of `/grr`, `/grr_sfari`, `/grr_seqpipe` under `$GRR_ROOT` **resolves** (`readlink -e`) **and** carries its `.CONTENTS.json.gz` manifest; otherwise it fails the build with `GRR not synced on this node yet: <repo>`. A dangling symlink (repo not yet synced) would otherwise bind-mount as an *empty* directory and die deep in the run with a baffling `FileNotFoundError: .CONTENTS.json`.

The same stage also pins `AGENT_UID` / `AGENT_GID` for compose. Declaring them only in the `environment{}` block is **not** sufficient — the exact bug gain-web-e2e #1042 shipped: compose silently took the `${AGENT_UID:-0}` *fallback* and every container ran as **root**. So the stage:

1. Re-derives the uid/gid in the shell (`id -u`, `id -g`) instead of trusting the `environment{}` block, and writes them plus `GRR_ROOT` to **`web_infra/.env`** — the compose *project directory*, where Compose auto-loads a `.env` from. (Gitignored.)
2. Passes **`--env-file web_infra/.env`** explicitly on every `docker compose` call, so nothing depends on which directory Compose picks as the project dir.
3. **Sources that same `.env`** (`set -a; . ./web_infra/.env; set +a`) before each call — because `--env-file` alone is *not* enough: the process environment **outranks** `--env-file`, so a variable that is present-but-**empty** in the shell still wins and still selects the fallback.

The `${AGENT_UID:-0}` fallback stays in the compose YAML as a last-resort guard for a plain local `docker compose up`; the `${GRR_ROOT:?...}` binds are hard-required (no default) so a missing `GRR_ROOT` fails loudly instead of mounting nothing.

### Build the prod images locally

CI pulls them from `registry.seqpipe.org`; locally we build from the repo wheels.

```bash
# from the gpf root
mkdir -p dist/core dist/web_api dist/gain

# 1. gain-core wheel (gpf-core depends on it)
cd ../gain && uv build --package gain-core --out-dir ../gpf/dist/gain && cd ../gpf

# 2. gpf-core + gpf-web wheels
uv build --package gpf-core --out-dir dist/core
uv build --package gpf-web  --out-dir dist/web_api

# 3. backend image (Django + gunicorn)
docker build -f web_api/Dockerfile.production    -t gpf-web-api-prod:local .

# 4. frontend image (Angular SPA + Apache reverse-proxy)
docker build -f web_ui/Dockerfile.production \
    --build-arg BACKEND_IMAGE=gpf-web-api-prod:local \
    -t gpf-web-ui-prod:local .

# 5. combined image (only needed for `STACK_MODE=combined`)
docker build -f Dockerfile.production \
    --build-arg BACKEND_IMAGE=gpf-web-api-prod:local \
    --build-arg FRONTEND_IMAGE=gpf-web-ui-prod:local \
    -t gpf-web-prod:local .
```

### Bring the stack up

Pick the overlay for the mode you want:

```bash
export BACKEND_IMAGE=gpf-web-api-prod:local
export FRONTEND_IMAGE=gpf-web-ui-prod:local
export COMBINED_IMAGE=gpf-web-prod:local         # only used in combined mode
export COMPOSE_PROJECT=gpf-web-e2e-local

# Node-local GRR root. Must hold grr/, grr_sfari/, grr_seqpipe/
# checkouts (materialized directory GRRs); the compose files bind each
# read-only at /grr, /grr_sfari, /grr_seqpipe. Required — there is no
# fallback (a missing GRR_ROOT fails the `${GRR_ROOT:?...}` bind loudly).
export GRR_ROOT="$HOME/grr-sync"
# Optional: run the non-root services as you, so the instance dir
# instance-import rewrites stays yours. This is what Jenkins does.
export AGENT_UID="$(id -u)" AGENT_GID="$(id -g)"

# Pick one:
export OVERLAY=web_infra/compose-jenkins-split.yaml      # split mode
# export OVERLAY=web_infra/compose-jenkins-combined.yaml # combined mode

# 1. Run instance-import to its completion
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml -f "$OVERLAY" \
    up -d db instance-import
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml -f "$OVERLAY" \
    wait instance-import
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml -f "$OVERLAY" \
    logs --no-color instance-import

# 2. Bring up the HTTP tier explicitly (mirrors Jenkinsfile.e2e —
#    explicit up so step 3's --no-deps doesn't trigger a re-import).
#    In split mode this brings up `backend` + `frontend`; in
#    combined mode just `frontend` (one supervisord container).
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml -f "$OVERLAY" \
    up -d mail frontend

# 3. Run the suite
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml -f "$OVERLAY" \
    run --rm --no-deps e2e-tests
```

### Iterate on a subset

```bash
# Single spec
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml -f "$OVERLAY" \
    run --rm --no-deps e2e-tests \
    npx playwright test --reporter=list tests/datasets.spec.ts

# Single test by name
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml -f "$OVERLAY" \
    run --rm --no-deps e2e-tests \
    npx playwright test --reporter=list -g "should display \"GPF"

# Sanity-check the API from inside the network
docker run --rm --network "${COMPOSE_PROJECT}_default" curlimages/curl:latest \
    sh -c 'curl -fsS http://frontend/api/v3/instance/version && echo'
```

### Tear down

```bash
docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml -f "$OVERLAY" \
    down -v --remove-orphans
```

`-v` removes the named MySQL volume; on next start `instance-import` re-runs from a clean DB.

### What's special about the compose stack

A few things differ from a vanilla `wdaemanage runserver` setup. They're load-bearing:

- **Apache (frontend) reverse-proxies `/api/`, `/ws/`, `/o/`, `/accounts/`** to the backend on port 9001. The SPA fallback `RewriteRule` excludes those prefixes so they don't get rewritten to `index.html`.
- **`/o/` and `/accounts/` are required for OAuth.** The SPA's log-in button does `window.location = /o/authorize/?...`, which the backend redirects to `/accounts/login/`. Both must be proxied.
- **Playwright workers are capped at 4 in CI** (`playwright.config.ts`). Local-dev (without `CI=1`) keeps Playwright's default.
- **`WDAE_EMAIL_VERIFICATION_ENDPOINT=http://frontend`.** Django bakes this URL into outbound mail; without it, the user-creation specs follow a `localhost:8000` link that chromium inside the network can't reach.
- **Backend logs are captured to `web_infra/wdae-logs/`.** `instance-import` and the active HTTP service (split-mode `backend` or combined-mode `frontend`) mount `./wdae-logs:/logs` and run with `WDAE_LOG_DIR=/logs`, so Django's `WatchedFileHandler` writes `wdae-debug.log` to a host bind that survives `compose down -v`. CI archives it (along with a wide combined `reports/web_e2e/compose.log` from `compose logs --no-color`) under the build's artefacts.

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
   # split mode: backend; combined mode: frontend (supervisord
   # forwards both gunicorn and apache stdio to its docker logs).
   docker compose -p "$COMPOSE_PROJECT" -f web_infra/compose-jenkins.yaml -f "$OVERLAY" \
       logs --no-color backend --tail 200
   ```
   or, on a CI build, grab the `wdae-debug.log` and `compose.log` artefacts archived by the Jenkins job — `wdae-debug.log` has the per-request Django output, `compose.log` interleaves every service's stdout by timestamp.
4. File a new issue: `gh issue create --repo iossifovlab/gpf --label needs-triage`. The umbrella `genomics-toolbox/CLAUDE.md` documents the label vocabulary and the workflow loop.
