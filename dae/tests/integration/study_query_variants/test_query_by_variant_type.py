# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("query_by_variant_type")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId momId sex status role
        f1       mom      0     0     2   1      mom
        f1       dad      0     0     1   1      dad
        f1       ch       dad   mom   2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom dad ch
chrA   1   .  A   C     .    .      .    GT     0/0 0/1 0/1
chrA   2   .  A   C     .    .      .    GT     0/1 0/1 0/1
chrA   3   .  A   AA    .    .      .    GT     0/0 0/1 0/1
chrA   4   .  AA  A     .    .      .    GT     0/0 0/1 0/1
chrA   5   .  AAA CCC   .    .      .    GT     0/0 0/1 0/1
        """)

    return vcf_study(
        root_path,
        "query_by_variant_type", pathlib.Path(ped_path),
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


@pytest.mark.parametrize(
    "begin, end, variant_type, count",
    [
        (1, 9, None, 5),
        (1, 9, "sub", 2),
        (1, 9, "ins", 1),
        (1, 9, "del", 1),
        (1, 9, "complex", 1),
        (1, 9, "comp", 1),
        (1, 9, "ins or del", 2),
        (1, 9, "sub or del", 3),
        (1, 9, "sub or ins", 3),
        (1, 9, "sub or complex", 3),
        (1, 9, "ins or del or complex", 3),
        (1, 9, "sub or ins or del or complex", 5),
        (1, 9, "sub or comp", 3),
        (1, 9, "ins or del or comp", 3),
        (1, 9, "sub or ins or del or comp", 5),
    ],
)
def test_query_by_variant_type(
    imported_study: GenotypeData,
    begin: int,
    end: int,
    variant_type: str | None,
    count: int,
) -> None:
    region = Region("chrA", begin, end)
    vs = list(imported_study.query_variants(
        regions=[region],
        variant_type=variant_type))
    assert len(vs) == count
