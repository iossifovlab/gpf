# ruff: file-ignore[implicit-namespace-package]
# A standalone script run by drive-import-genotypes.sh, not a package
# member -- nothing imports it.
"""Dump one study of a GPF instance as a sorted TSV.

Usage: dump_study.py <gpf_instance.yaml> <study id>

Run by drive-import-genotypes.sh after the import, as a separate process:
it builds the instance from its configuration, loads the study and
queries every variant. This is the second, independent read of what
import_genotypes wrote. The output is the file that
readback-import-genotypes.sh checks:

    #families<TAB>f1,f2
    family<TAB>chrom<TAB>pos<TAB>ref<TAB>alt<TAB>best_state
    f1<TAB>chrA<TAB>11<TAB>A<TAB>C<TAB>2 2 1/0 0 1
    ...

best_state has one row per allele (reference first), with the count of
that allele for each family member, in the format of the input file.
Exits 1 when the study is missing.
"""

import sys

from gpf.gpf_instance import GPFInstance


def main(argv: list[str]) -> int:
    try:
        config, study_id = argv
    except ValueError:
        print(__doc__, file=sys.stderr)
        return 2
    instance = GPFInstance.build(config)
    study = instance.get_genotype_data(study_id)
    if study is None:
        print(f"dump_study: no study {study_id!r} in {config}", file=sys.stderr)
        return 1

    rows = []
    for variant in study.query_variants():
        best_state = "/".join(
            " ".join(str(count) for count in row)
            for row in variant.best_state.tolist()
        )
        rows.extend(
            (variant.family_id, allele.chrom, allele.position,
             allele.reference, allele.alternative, best_state)
            for allele in variant.alt_alleles
        )

    print("#families\t" + ",".join(sorted(study.families.keys())))
    print("family\tchrom\tpos\tref\talt\tbest_state")
    for row in sorted(rows):
        print("\t".join(str(field) for field in row))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
