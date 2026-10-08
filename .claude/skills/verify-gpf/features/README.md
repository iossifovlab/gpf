# verify-gpf features

Each file here describes one user-facing CLI feature of `gpf` and how
`verify-gpf` drives it. The drive recipes and helpers are in `../SKILL.md`.

## Baseline preconditions

- The checkout has its own `.venv`, so `.venv/bin/import_genotypes` exists
  and `gpf` imports from this checkout's `core/gpf`. gpf consumes `gain` as
  a wheel in `dist/gain/` (see `CLAUDE.md`). In a fresh worktree:

  ```bash
  # from a gain checkout at origin/master (never the gpf worktree)
  uv build --package gain-core --wheel --out-dir <gpf worktree>/dist/gain
  # from the gpf worktree
  uv sync --find-links ./dist/gain --upgrade-package gain-core
  ```

  `--upgrade-package gain-core` is needed when the wheel that `uv.lock`
  pins is older than the gpf source needs (an `ImportError` from a
  `gain.*` module). It rewrites `uv.lock` in the worktree. Never commit
  that change: gpf CI locks against gain master's wheel itself.
- `core/tests/small/tools/fixtures/repo` is in the checkout (it is
  committed; no submodule).
- A run was launched (`scripts/launch.sh`) and Doctor (`scripts/doctor.sh
  <run id>`) passes.
- No network, no docker, no `~/.grr_definition.yaml` and no shared GPF
  instance. Each run builds its own instance in scratch.

## Driving conventions

- Call the checkout CLI as `.venv/bin/<tool>`, never the bare name from
  `PATH`: a conda env can shadow it.
- Pass the run's instance, `.verify/<run id>/scratch/instance/gpf_instance.yaml`,
  as `-i`. The drives also set `GRR_DEFINITION_FILE` to
  `.verify/<run id>/scratch/grr.yaml` and `DAE_DB_DIR` to the run's
  instance directory.
- Run with `HOME` and `TMPDIR` inside `.verify/<run id>/scratch/` and write
  every input, output, instance and work directory there too.
- Use `-j 1` so a run is deterministic and a failure is one readable
  traceback.

## Proof rules

- A drive proves a feature only with its evidence kept in
  `.verify/<run id>/evidence/<feature>/`: the command, stdout, stderr, the
  exit code and the output.
- What a drive wrote into the instance is read back a second time by a
  separate process, and the read-back compares exact expected values.
- Pick inputs whose expected values differ from each other and from the
  default (`0`, empty, `NA`), so a broken drive cannot pass by accident.
- The run writes only inside `.verify/<run id>/`; after Cleanup,
  `git status --porcelain` shows no run output, and
  `git status --porcelain core/tests/small/tools/fixtures` prints nothing.
- A drive never writes the committed fixture: Launch copies the fixture GRR
  to scratch, and the instance lives in scratch.

## Feature index

| Feature file | CLI | Instance | Drive helper |
| --- | --- | --- | --- |
| [import-genotypes.md](import-genotypes.md) | `import_genotypes` | the run's scratch instance over a copy of `core/tests/small/tools/fixtures/repo` (`genomes/mock`, `gene_models/mock`) | `scripts/drive-import-genotypes.sh` |
