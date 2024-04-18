# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pathlib

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def summary_stats(
        tmp_path_factory: pytest.TempPathFactory,
        impala_genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"summary_stats_{impala_genotype_storage.storage_id}")
    gpf_instance = alla_gpf(root_path, impala_genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
familyId personId dadId   momId  sex status role phenotype
f1       f1.mom   0       0      2   1      mom  unaffected
f1       f1.dad   0       0      1   1      dad  unaffected
f1       f1.p1    f1.dad  f1.mom 1   2      prb  autism
f1       f1.s1    f1.dad  f1.mom 2   2      sib  autism
f2       f2.mom   0       0      2   1      mom  unaffected
f2       f2.dad   0       0      1   1      dad  unaffected
f2       f2.p1    f2.dad  f2.mom 1   2      prb  autism
f2       f2.s1    f2.dad  f2.mom 2   2      sib  autism
f3       f3.mom   0       0      2   1      mom  unaffected
f3       f3.dad   0       0      1   1      dad  unaffected
f3       f3.p1    f3.dad  f3.mom 1   2      prb  autism
f3       f3.s1    f3.dad  f3.mom 2   2      sib  autism
f4       f4.mom   0       0      2   1      mom  unaffected
f4       f4.dad   0       0      1   1      dad  unaffected
f4       f4.p1    f4.dad  f4.mom 1   2      prb  autism
f4       f4.s1    f4.dad  f4.mom 2   2      sib  autism
f5       f5.mom   0       0      2   1      mom  unaffected
f5       f5.dad   0       0      1   1      dad  unaffected
f5       f5.p1    f5.dad  f5.mom 1   2      prb  autism
f5       f5.s1    f5.dad  f5.mom 2   2      sib  autism
        """)

    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
##contig=<ID=1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT f1.mom f1.dad f1.p1 f1.s1 f2.mom f2.dad f2.p1 f2.s1 f3.mom f3.dad f3.p1 f3.s1 f4.mom f4.dad f4.p1 f4.s1 f5.mom f5.dad f5.p1 f5.s1
chrA   1   .  A   C,G,T .    .      .    GT     1/3    2/3    1/3   1/2   1/2    2/3    2/3   2/2   1/2    3/3    1/3   2/3   1/2    2/3    2/3   1/2   2/3    1/2    2/1   1/3
chrA   2   .  A   C,G,T .    .      .    GT     1/3    2/3    1/3   1/2   1/2    2/3    2/3   2/2   1/2    3/3    1/3   2/3   1/2    2/3    2/3   1/2   ./.    ./.    ./.   ./.
chrA   3   .  A   C,G,T .    .      .    GT     1/2    1/2    1/1   2/2   0/2    0/2    0/2   2/2   1/2    1/2    1/2   2/2   2/3    2/3    2/3   2/2   0/3    0/3    3/3   0/0
        """)  # noqa

    study = vcf_study(
        root_path,
        "summary_stats", pathlib.Path(ped_path),
        [pathlib.Path(vcf_path)],
        gpf_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "include_reference_genotypes": True,
                    "include_unknown_family_genotypes": True,
                    "include_unknown_person_genotypes": True,
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                },
            },
            "processing_config": {
                "include_reference": True,
            },
        })
    return study


def test_summary_stats_simple(summary_stats: GenotypeData) -> None:

    vs = list(summary_stats.query_variants(
        return_unknown=True, return_reference=True))

    assert len(vs) == 15


@pytest.mark.parametrize("regions,sv_count,fv_count", [
    ([Region("chrA", 1, 1)], 1, 5),
    ([Region("chrA", 2, 2)], 1, 4),
    ([Region("chrA", 1, 2)], 2, 9),
    ([Region("chrA", 3, 3)], 3, 8),
    ([Region("chrA", 1, 3)], 5, 17),
])
def test_summary_stats_summary(
        summary_stats: GenotypeData,
        regions: list[Region],
        sv_count: int,
        fv_count: int) -> None:

    vs = list(summary_stats.query_summary_variants(
        regions=regions,
    ))
    assert len(vs) == sv_count

    result = 0
    for v in vs:
        for aa in v.matched_alleles:
            print(aa, aa.get_attribute("family_variants_count"))
        result += max(
            aa.get_attribute("family_variants_count")
            for aa in v.alt_alleles)

    assert result == fv_count
