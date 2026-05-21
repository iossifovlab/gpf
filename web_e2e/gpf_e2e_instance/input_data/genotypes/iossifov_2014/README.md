# iossifov_2014 e2e fixture

This directory holds the input data for the `iossifov_2014_liftover` study used by the GPF web_e2e Playwright suite.

## Files

- `IossifovWE2014.ped` — full Iossifov 2014 pedigree (untouched).
- `IossifovWE2014.tsv` — full hg19 de novo variants (untouched; referenced only by `profile.sh` for local profiling).
- `IossifovWE2014_liftover.tsv` — full hg19+hg38 liftover TSV (untouched; kept as the reference unstripped dataset).
- `IossifovWE2014_liftover_chr1_14_X.tsv` — **what the e2e import actually consumes** (`import_project.yaml` points here). Chromosome-restricted subset of the liftover TSV: chr1 + chr14 + chrX only (892 variants out of 5,644).

## Why the stripped TSV

Importing the full 5,644-variant set through the annotation pipeline (gnomAD exomes + gnomAD genomes + dbSNP + ClinVar + MPC + liftover + normalize_allele) dominates the e2e Jenkins build time. Restricting to three chromosomes cuts annotation work ~6× without removing any specs' code paths — the kept chromosomes are chosen to cover the regions referenced by `web_e2e/tests/*.spec.ts`.

## Regenerating the stripped TSV

```bash
awk -F'\t' 'NR==1 || $1 ~ /^chr(1|14|X)$/' \
    IossifovWE2014_liftover.tsv \
    > IossifovWE2014_liftover_chr1_14_X.tsv
```

If you change the keep-set, rename the file accordingly (e.g. `_chr1_4_13_14_X.tsv`) and update `import_project.yaml` to match — the filename is intentionally self-documenting so the scope can't drift silently.
