# import-genotypes

## Sub-features

- `import_genotypes <import project>` reads a pedigree and a de novo
  variants file and imports them as one study into a GPF instance.
- The import project names the inputs (`input.pedigree`, `input.denovo`),
  the work directory (`processing_config.work_dir`) and the genotype
  storage (`destination.storage_id`).
- The de novo loader reads the columns `location` (`chrom:pos`), `variant`
  (`sub(REF->ALT)`), `familyId` and `bestState` (one row per allele, a count
  for each family member).
- The import writes the study configuration into
  `<instance>/studies/<study id>/<study id>.yaml` and the parquet tables
  (`pedigree`, `meta`, `summary`, `family`) under the storage's `base_dir`.
- After the import, `GPFInstance.get_genotype_data(<study id>)` finds the
  study, and `query_variants()` returns its variants.

## How to get to it (user POV)

A user writes an import project and runs:

```bash
import_genotypes -i <instance>/gpf_instance.yaml -j 1 import_project.yaml
```

The tool runs its import tasks and exits 0. The study then appears in the
instance: in the genotype browser of a GPF web server that serves the
instance, or from Python with `GPFInstance.build(<config>)`.

## Driving it with verify-gpf

```bash
.claude/skills/verify-gpf/scripts/drive-import-genotypes.sh "$RUN_ID"
```

- **Instance:** the run's scratch instance from `launch.sh`, over a copy of
  the fixture GRR: `genomes/mock` (one chromosome `chrA`, 100 bases, all
  `A`) and `gene_models/mock` (no genes). The genotype storage is
  `verify_duckdb` (`duckdb_parquet`) in the instance directory.
- **Inputs:** two trio families, `f1` (male proband) and `f2` (female
  proband), and three de novo variants: `f1 chrA:11 A>C`, `f1 chrA:23 A>G`
  and `f2 chrA:37 A>T`, each in the proband only (`2 2 1/0 0 1`). Every
  reference allele is `A`, because the genome is all `A`. The positions and
  the alternative alleles all differ, so a dropped, moved or swapped variant
  cannot pass.
- **Output:** `study.yaml`, `storage_files.txt`, and `variants.tsv`, the dump
  of the study by `scripts/dump_study.py` in a separate process.
- **Read-back:** `scripts/readback-import-genotypes.sh variants.tsv` checks
  the families `f1`, `f2` and exactly the three variants with their best
  states. A copy of the dump with one alternative allele changed fails it
  (exit 1).

## Gotchas

- **Use `core/tests/small/tools/fixtures/`, not `web_e2e/gpf_e2e_instance/`.**
  The e2e instance's `grr-definition.yaml` reads the directory GRRs
  `/grr_sfari`, `/grr` and `/grr_seqpipe`, which exist only on the Jenkins
  agents, and its `import_data.sh` deletes data inside the instance
  directory. The tools fixture is a committed directory GRR that needs no
  network.
- **The instance has no annotation.** The fixture's `annotation.yaml` names
  `scores/mock1` and `scores/mock2`, but their data files (`mock_file`) are
  20-byte placeholders (`type: mock_resource`), not score tables. An
  instance that loads that annotation cannot annotate. The read-back
  therefore checks genotypes (families, positions, alleles, best states),
  not scores.
- **`import_genotypes` does not check a de novo reference allele against
  the genome.** A record `chrA:11 sub(C->T)` imports with exit 0 and reads
  back as `C>T`, although `genomes/mock` is 100 x `A`. Keep every reference
  allele `A`, so the inputs stay true to the genome; a wrong reference in an
  input is not caught by the import.
- **A stale gain wheel fails at import time, not in Doctor's `PATH`
  check.** When `uv.lock` pins a gain wheel older than the gpf source,
  `import_genotypes` fails with `ModuleNotFoundError: No module named
  'gain.…'`. Doctor's import check catches it; set up the `.venv` as
  `features/README.md` says.
- **`dump_stderr.txt` holds a deprecation warning.** Building the instance
  logs "no `work_dir` passed to `build_annotation_pipeline`". It does not
  affect the dump; the dump's exit code is in `dump_exit_code.txt`.
- **One study per run.** The drive refuses an instance that already has
  `verify_study`; launch a new run to drive it again.
