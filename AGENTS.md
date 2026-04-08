# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GPF (Genotypes and Phenotypes in Families) is a system for managing large databases of genetic variants and phenotypic measurements from family collections (e.g., the Simons Simplex Collection with ~2,600 autism families).

## Environment Setup

**This project requires conda/mamba.** All tools must be installed via conda, not system pip.

```bash
mamba env create --name gpf --file ./environment.yml
mamba env update --name gpf --file ./dev-environment.yml
conda activate gpf

# Install core packages in editable mode
pip install -e gain_core
pip install -e gpf_core
pip install -e gpf_web
```

## Commands

### Testing

```bash
# Run a single test file
cd gpf_core && pytest -v tests/small/path/to/test_file.py

# Run a test module
cd gpf_core && pytest -v tests/small/module/

# Run GAIN tests in parallel
cd gain_core && pytest -v -n 10 tests/

# Run GPF tests in parallel
cd gpf_core && pytest -v -n 10 tests/

# Run GPF Web tests in parallel
cd gpf_web && pytest -v -n 5 gpf_web/
```

Test markers in `gpf_core/pytest.ini`: genotype storage (`gs_impala`, `gs_impala2`, `gs_inmemory`, `gs_gcp`, `gs_duckdb`, `gs_duckdb_parquet`, `gs_schema2`, `gs_parquet` and `no_gs_*` exclusion variants) and GRR (`grr_rw`, `grr_ro`, `grr_full`, `grr_http`, `grr_tabix`). Tests run with `PYTHONHASHSEED=0`.

Test markers in `gain_core/pytest.ini`: `grr_rw`, `grr_ro`, `grr_full`, `grr_http`, `grr_tabix`.

### Linting and Type Checking

```bash
# Ruff linting (fast, primary linter)
ruff check --fix .

# Type checking (slow, 2-5 minutes)
mypy gain --exclude gain_core/docs/ --exclude gain_core/gain/docs/
mypy gpf --exclude gpf_core/docs/
mypy gpf_web --exclude gpf_web/docs/ --exclude gpf_web/conftest.py
```

Config: `ruff.toml` (line-length: 80, target: py310), `mypy.ini` (strict, Django plugin).

### Pre-commit Hook

```bash
cp pre-commit .git/hooks/
```

### Test Infrastructure (Docker)

Some tests require external services. Start them with:

```bash
docker compose up -d
```

Services defined in `docker-compose.yaml`:
- **MinIO** (ports 9000/9001) — S3-compatible object storage for GCP/S3 storage tests; credentials `minioadmin/minioadmin`, bucket `test-bucket`
- **Apache httpd** (port 28080) — HTTP fixture server for `grr_http` tests; serves `gain_core/tests/.test_grr/`

### Do NOT run locally

`build.sh` requires Docker and a private `build-scripts` submodule — it's only for CI (Jenkins).

## Architecture

### Package Structure

- **`gain_core/`** — GAIn (Genomic Annotation Infrastructure): annotation engine, genomic resources, effect annotation, task graph, gene scores/sets
- **`gpf_core/`** — GPF core library: genotype storage, studies, pedigrees, pheno, import tools, query API (Python package `gpf`, depends on `gain`)
- **`gpf_web/`** — Web Django Application: REST API on top of GPF (Django 5.2)
- **`impala_storage/`**, **`impala2_storage/`**, **`gcp_storage/`** — optional storage backends
- **`federation/`** — federated query support
- **`rest_client/`** — REST API client library
- **`*_annotator/`** — external annotation plugins (VEP, SpliceAI, demo)

### Plugin System

GPF uses Python entry points for extensibility. Entry point group names use the `dae.*` prefix for backward compatibility even when defined in `gain`.

**Defined in `gain_core/setup.py`:**
1. **Genomic Resource Implementations** (`dae.genomic_resources.implementations`): position/allele scores, liftover chain, genome, gene models, CNV collections, annotation pipelines
2. **Annotators** (`dae.annotation.annotators`): score annotators, effect annotator, gene set annotator, liftover, normalize allele, CNV collection, chrom mapping

**Defined in `gpf_core/setup.py`:**
3. **Genomic Resource Implementations** (`dae.genomic_resources.implementations`): gene sets, gene scores
4. **Genotype Storage Factories** (`dae.genotype_storage.factories`): inmemory, duckdb (multiple variants including S3 and Parquet), parquet

### GAIN Submodules (`gain_core/gain/`)

- **`annotation/`** — annotation pipeline engine
- **`genomic_resources/`** — Genomic Resource Repository (GRR), resource implementations and plugins; supports HTTP/S3 access
- **`effect_annotation/`** — variant effect annotation
- **`task_graph/`** — DAG-based task orchestration
- **`gene_scores/`**, **`gene_sets/`**, **`genomic_scores/`** — score and set resource types
- **`utils/`** — shared utilities

### GPF Core Submodules (`gpf_core/gpf/`)

- **`genotype_storage/`** — factory pattern for pluggable storage backends
- **`variants/`** — variant data structures and operations
- **`studies/`** — study and dataset management
- **`pedigrees/`** — family/pedigree handling
- **`pheno/`** — phenotypic data import and browser
- **`enrichment_tool/`** — gene enrichment analysis
- **`import_tools/`** — data import pipelines
- **`duckdb_storage/`**, **`parquet_storage/`** — built-in storage implementations
- **`query_variants/`** — query API for variant retrieval

### GPF Web Django Apps (`gpf_web/gpf_web/`)

Key apps: `datasets_api`, `genotype_browser`, `enrichment_api`, `family_api`, `gene_profiles_api`, `person_sets_api`, `pheno_browser_api`, `users_api`, `groups_api`, `gpf_instance`, `studies`.

Key patterns:
- `QueryBaseView` — base class for variant query endpoints
- `StreamingHttpResponse` — used for large result sets
- `WGPFInstance` — web-layer wrapper around GPFInstance
- OAuth2 toolkit for multi-tenant authentication

### Data Flow

```
REST Request → GPF Web Django App
                → QueryTransformer (request normalization)
                → GPF Core (GPFInstance / study)
                    → Genotype Storage (DuckDB / Parquet / Impala)
                    → Annotation Engine
                    → Genomic Resource Repository
                → ResponseTransformer (result formatting)
              → StreamingHttpResponse
```

## Key Dependencies

- **Python 3.12**, Django 5.2, DRF 3.16
- **DuckDB 1.5** — primary embedded storage
- **dask** — parallel computing
- **pandas**, **numpy**, **pyarrow** — data analysis
- **pysam** — SAM/BAM file handling
- **pydantic** — data validation
- **Sentry SDK** — error tracking in production

## Django Settings

Multiple settings files in `gpf_web/gpf_web/gpf_web/`: `settings.py`, `test_settings.py`, `default_settings.py`, `gunicorn_settings.py`, `mypy_settings.py`.

<!-- BEGIN BEADS INTEGRATION v:2 profile:minimal -->
## Beads Issue Tracker

This project uses **br (beads_rust)** for issue tracking.

**Note:** `br` is non-invasive and never executes git
commands. After `br sync --flush-only`, you must manually
run `git add .beads/ && git commit`.

### Quick Reference

```bash
br ready              # Find available work
br show <id>          # View issue details
br update <id> --claim  # Claim work
br close <id>         # Complete work
br sync --flush-only  # Export JSONL
git add .beads/
git commit -m "sync beads"
```

### Rules

- Use `br` for ALL task tracking — do NOT use
  TodoWrite, TaskCreate, or markdown TODO lists
- Use `br remember` for persistent knowledge — do NOT
  use MEMORY.md files

<!-- END BEADS INTEGRATION -->

### Using bv as an AI sidecar

bv is a graph-aware triage engine for Beads projects (.beads/beads.jsonl). Instead of parsing JSONL or hallucinating graph traversal, use robot flags for deterministic, dependency-aware outputs with precomputed metrics (PageRank, betweenness, critical path, cycles, HITS, eigenvector, k-core).

**Scope boundary:** bv handles *what to work on* (triage, priority, planning). For agent-to-agent coordination (messaging, work claiming, file reservations), use [MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail).

**⚠️ CRITICAL: Use ONLY `--robot-*` flags. Bare `bv` launches an interactive TUI that blocks your session.**

#### The Workflow: Start With Triage

**`bv --robot-triage` is your single entry point.** It returns everything you need in one call:
- `quick_ref`: at-a-glance counts + top 3 picks
- `recommendations`: ranked actionable items with scores, reasons, unblock info
- `quick_wins`: low-effort high-impact items
- `blockers_to_clear`: items that unblock the most downstream work
- `project_health`: status/type/priority distributions, graph metrics
- `commands`: copy-paste shell commands for next steps

bv --robot-triage        # THE MEGA-COMMAND: start here
bv --robot-next          # Minimal: just the single top pick + claim command

# Token-optimized output (TOON) for lower LLM context usage:
bv --robot-triage --format toon
export BV_OUTPUT_FORMAT=toon
bv --robot-next

#### Other Commands

**Planning:**
| Command | Returns |
|---------|---------|
| `--robot-plan` | Parallel execution tracks with `unblocks` lists |
| `--robot-priority` | Priority misalignment detection with confidence |

**Graph Analysis:**
| Command | Returns |
|---------|---------|
| `--robot-insights` | Full metrics: PageRank, betweenness, HITS (hubs/authorities), eigenvector, critical path, cycles, k-core, articulation points, slack |
| `--robot-label-health` | Per-label health: `health_level` (healthy\|warning\|critical), `velocity_score`, `staleness`, `blocked_count` |
| `--robot-label-flow` | Cross-label dependency: `flow_matrix`, `dependencies`, `bottleneck_labels` |
| `--robot-label-attention [--attention-limit=N]` | Attention-ranked labels by: (pagerank × staleness × block_impact) / velocity |

**History & Change Tracking:**
| Command | Returns |
|---------|---------|
| `--robot-history` | Bead-to-commit correlations: `stats`, `histories` (per-bead events/commits/milestones), `commit_index` |
| `--robot-diff --diff-since <ref>` | Changes since ref: new/closed/modified issues, cycles introduced/resolved |

**Other Commands:**
| Command | Returns |
|---------|---------|
| `--robot-burndown <sprint>` | Sprint burndown, scope changes, at-risk items |
| `--robot-forecast <id\|all>` | ETA predictions with dependency-aware scheduling |
| `--robot-alerts` | Stale issues, blocking cascades, priority mismatches |
| `--robot-suggest` | Hygiene: duplicates, missing deps, label suggestions, cycle breaks |
| `--robot-graph [--graph-format=json\|dot\|mermaid]` | Dependency graph export |
| `--export-graph <file.html>` | Self-contained interactive HTML visualization |

#### Scoping & Filtering

bv --robot-plan --label backend              # Scope to label's subgraph
bv --robot-insights --as-of HEAD~30          # Historical point-in-time
bv --recipe actionable --robot-plan          # Pre-filter: ready to work (no blockers)
bv --recipe high-impact --robot-triage       # Pre-filter: top PageRank scores
bv --robot-triage --robot-triage-by-track    # Group by parallel work streams
bv --robot-triage --robot-triage-by-label    # Group by domain

#### Understanding Robot Output

**All robot JSON includes:**
- `data_hash` — Fingerprint of source beads.jsonl (verify consistency across calls)
- `status` — Per-metric state: `computed|approx|timeout|skipped` + elapsed ms
- `as_of` / `as_of_commit` — Present when using `--as-of`; contains ref and resolved SHA

**Two-phase analysis:**
- **Phase 1 (instant):** degree, topo sort, density — always available immediately
- **Phase 2 (async, 500ms timeout):** PageRank, betweenness, HITS, eigenvector, cycles — check `status` flags

**For large graphs (>500 nodes):** Some metrics may be approximated or skipped. Always check `status`.

#### jq Quick Reference

bv --robot-triage | jq '.quick_ref'                        # At-a-glance summary
bv --robot-triage | jq '.recommendations[0]'               # Top recommendation
bv --robot-plan | jq '.plan.summary.highest_impact'        # Best unblock target
bv --robot-insights | jq '.status'                         # Check metric readiness
bv --robot-insights | jq '.Cycles'                         # Circular deps (must fix!)
bv --robot-label-health | jq '.results.labels[] | select(.health_level == "critical")'

**Performance:** Phase 1 instant, Phase 2 async (500ms timeout). Prefer `--robot-plan` over `--robot-insights` when speed matters. Results cached by data hash.

Use bv instead of parsing beads.jsonl—it computes PageRank, critical paths, cycles, and parallel tracks deterministically.
