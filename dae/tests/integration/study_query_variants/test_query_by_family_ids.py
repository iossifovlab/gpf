# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"query_by_family_path_{genotype_storage.storage_id}")
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        mom1      0      0      2    1       mom
        f1        dad1      0      0      1    1       dad
        f1        ch1       dad1   mom1   2    2       prb
        f2        mom2      0      0      2    1       mom
        f2        dad2      0      0      1    1       dad
        f2        ch2       dad2   mom2   2    2       prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 dad2 ch2 mom2
chrA   1   .  A   G     .    .      .    GT     0/0  0/1  0/0 0/1  0/0 0/0
chrA   2   .  A   G     .    .      .    GT     1/1  1/1  0/0 1/1 0/0  1/1
        """)

    return vcf_study(
        root_path,
        "minimal_vcf", ped_path, [vcf_path],
        gpf_instance)


@pytest.mark.parametrize(
    "region,family_ids,count",
    [
        (Region("chrA", 1, 1), ["f1"], 1),
        (Region("chrA", 1, 1), ["f2"], 1),
        (Region("chrA", 1, 1), ["f1", "f2"], 2),
        (Region("chrA", 1, 1), [], 0),
        (Region("chrA", 1, 1), None, 2),
        (Region("chrA", 1, 2), ["f1"], 2),
        (Region("chrA", 1, 2), ["f2"], 2),
        (Region("chrA", 1, 2), ["f1", "f2"], 4),
        (Region("chrA", 1, 2), [], 0),
        (Region("chrA", 1, 2), None, 4),
    ],
)
def test_query_by_family_ids(
        imported_study: GenotypeData,
        region: Region,
        family_ids: list[str], count: int) -> None:
    vs = list(imported_study.query_variants(
        regions=[region], family_ids=family_ids))
    assert len(vs) == count
