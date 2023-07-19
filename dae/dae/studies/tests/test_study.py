# pylint: disable=W0621,C0114,C0116,W0212,W0613
import time

import pytest

from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.acgt_import import acgt_gpf


def test_can_get_test_study(quads_f1: GenotypeData) -> None:
    assert quads_f1 is not None


def test_can_get_all_variants(quads_f1: GenotypeData) -> None:
    variants = quads_f1.query_variants()
    variants = list(variants)

    assert len(variants) == 3


def test_can_query_effect_groups(quads_f1: GenotypeData) -> None:
    variants = quads_f1.query_variants(effect_types=["noncoding"])
    variants = list(variants)

    assert len(variants) == 3

    no_variants = quads_f1.query_variants(effect_types=["lgds"])
    no_variants = list(no_variants)

    assert len(no_variants) == 0


def test_can_close_query(quads_f1: GenotypeData) -> None:
    variants = quads_f1.query_variants()

    for v in variants:
        print(v)
        break

    variants.close()
    time.sleep(0.1)


@pytest.fixture(scope="module")
def ps_study(tmp_path_factory: pytest.TempPathFactory) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        "person_set_collection_test_study")
    gpf_instance = acgt_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
f3       mom3     0     0     2   1      mom
f3       dad3     0     0     1   1      dad
f3       ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   1   .  A   C   .    .      .    GT     0/0  0/0  0/1 0/0  0/0  0/0
chr1   2   .  C   G   .    .      .    GT     0/0  0/0  0/0 0/0  0/1  0/1
chr1   3   .  G   T   .    .      .    GT     0/0  1/0  0/0 0/0  0/0  0/0
        """)  # noqa
    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            }
        },
    }
    return vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        gpf_instance,
        project_config_update=project_config_update)


def test_can_query_person_sets(ps_study: GenotypeData) -> None:
    genotype_study = ps_study

    vs = list(ps_study.query_variants())
    assert len(vs) == 3

    ps_query = ("status", ["affected"])
    vs = list(genotype_study.query_variants(person_set_collection=ps_query))
    assert len(vs) == 2

    ps_query = ("status", ["unaffected"])
    vs = list(genotype_study.query_variants(person_set_collection=ps_query))
    assert len(vs) == 2

    ps_query = ("status", ["unaffected", "affected"])
    vs = list(genotype_study.query_variants(person_set_collection=ps_query))
    assert len(vs) == 3
