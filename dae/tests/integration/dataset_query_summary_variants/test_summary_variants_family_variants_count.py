# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_dataset, setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_dataset(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        "test_summary_variants_family_variants_count")
    gpf_instance = alla_gpf(root_path, genotype_storage_factory(root_path))
    ped_path1 = setup_pedigree(
        root_path / "study_1" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chrA>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
        chrA   1   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0 0/0 0/1
        chrA   2   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/0 0/0 0/1
        chrA   3   .  A   T    .    .      .    GT     1/0 0/0 0/0 0/0 0/0 0/0
        chrA   4   .  A   T    .    .      .    GT     0/1 0/0 0/0 0/1 0/0 0/0
        """)
    study1 = vcf_study(
        root_path,
        "study_1", ped_path1, [vcf_path1],
        gpf_instance)

    ped_path2 = setup_pedigree(
        root_path / "study_2" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    vcf_path2 = setup_vcf(
        root_path / "study_2" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chrA>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
        chrA   1   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0 0/0 0/1
        chrA   2   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/0 0/0 0/1
        chrA   3   .  A   T    .    .      .    GT     1/0 0/0 0/0 0/0 0/0 0/0
        chrA   4   .  A   T    .    .      .    GT     0/1 0/0 0/0 0/1 0/0 0/0
        """)

    study2 = vcf_study(
        root_path,
        "study_2", ped_path2, [vcf_path2],
        gpf_instance)

    return setup_dataset(
        "ds1", gpf_instance, study1, study2,
        dataset_config_update=f"conf_dir: {root_path}",
    )


@pytest.mark.parametrize("region,family_variants_count", [
    (Region("chrA", 1, 1), 4),
    (Region("chrA", 2, 2), 2),
    (Region("chrA", 3, 3), 2),
    (Region("chrA", 4, 4), 4),
])
def test_summary_variants_family_variants_count_single_allele(
    region: Region, family_variants_count: int, imported_dataset: GenotypeData,
) -> None:

    assert imported_dataset is not None
    svs = list(imported_dataset.query_summary_variants(regions=[region]))
    assert len(svs) == 1
    assert len(svs[0].alt_alleles) == 1
    aa = svs[0].alleles[1]
    assert aa.get_attribute("family_variants_count") == family_variants_count
