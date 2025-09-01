# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.acgt_import import acgt_gpf


@pytest.fixture(scope="module")
def quads_f1_study(tmp_path_factory: pytest.TempPathFactory) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        "quads_f1")
    gpf_instance = acgt_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       prb1     dad1  mom1  1   2      prb
f1       sib1     dad1  mom1  2   2      sib
        """)
    vcf_path = setup_vcf(
        root_path / "quads_f1" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 prb1 sib1
chr1   1   .  A   C   .    .      .    GT     0/1  0/0  0/1  0/0
chr2   1   .  A   C   .    .      .    GT     0/0  0/1  0/1  0/0
chr3   1   .  A   C   .    .      .    GT     0/0  0/1  0/0  0/1
        """)
    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
                "omission_mode": "omission",
            },
        },
    }
    return vcf_study(
        root_path,
        "quads_f1", ped_path, [vcf_path],
        gpf_instance=gpf_instance,
        project_config_update=project_config_update)


def test_can_get_test_study(quads_f1_study: GenotypeData) -> None:
    assert quads_f1_study is not None


def test_can_get_all_variants(quads_f1_study: GenotypeData) -> None:

    variants = list(quads_f1_study.query_variants())

    assert len(variants) == 3


def test_can_query_effect_groups(quads_f1_study: GenotypeData) -> None:
    variants = list(quads_f1_study.query_variants(
        effect_types=["noncoding"]))

    assert len(variants) == 3

    no_variants = list(quads_f1_study.query_variants(
        effect_types=["lgds"]))

    assert len(no_variants) == 0


def test_can_query_coding_effect_group(quads_f1_study: GenotypeData) -> None:
    variants = list(quads_f1_study.query_variants(
        effect_types=["coding"]))

    assert len(variants) == 0
