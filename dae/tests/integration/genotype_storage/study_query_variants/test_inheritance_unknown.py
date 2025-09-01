# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable
from typing import cast

import pytest
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyAllele


@pytest.fixture(scope="module")
def nontrio_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_inheritance_unknown")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
familyId personId dadId momId sex status role
f1       dad1     gpa1  0     1    1     dad
f1       ch1      dad1  0     2    2     prb
f2       mom2     0     0     2    1     mom
f2       dad2     0     0     1    1     dad
f2       ch2      dad2  mom2  2    2     prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mis1 dad1 ch1 mis2 dad2 ch2 mom2
chrA   1   .  A   G   .    .      .    GT     0/0  0/0  ./0 0/0  0/0  0/0 0/0
chrA   2   .  A   G   .    .      .    GT     0/0  0/0  1/0 0/0  0/0  0/0 0/0
chrA   3   .  A   G,C .    .      .    GT     0/0  0/1  1/0 0/0  0/0  0/0 0/0
chrA   4   .  A   G,C .    .      .    GT     0/0  1/1  1/1 0/0  0/0  0/0 0/0
chrA   5   .  A   G,C .    .      .    GT     0/0  2/1  2/1 0/0  0/0  0/0 0/0
chrA   6   .  A   G,C .    .      .    GT     0/0  2/2  2/2 0/0  0/0  0/0 0/0
        """)

    return vcf_study(
        root_path,
        "test_inheritance_unknown", pathlib.Path(ped_path),
        [vcf_path],
        gpf_instance=gpf_instance,
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
    "region,inheritance",
    [
        (Region("chrA", 1, 1), Inheritance.unknown),
        (Region("chrA", 2, 2), Inheritance.unknown),
        (Region("chrA", 3, 3), Inheritance.unknown),
        (Region("chrA", 4, 4), Inheritance.unknown),
        (Region("chrA", 5, 5), Inheritance.unknown),
        (Region("chrA", 6, 6), Inheritance.unknown),
    ],
)
def test_inheritance_nontrio(
    nontrio_study: GenotypeData,
    region: Region,
    inheritance: Inheritance,
) -> None:
    vs = list(nontrio_study.query_variants(
        regions=[region],
        family_ids=["f1"],
        return_reference=True,
        return_unknown=True))

    assert len(vs) == 1
    for v in vs:
        for aa in v.alt_alleles:
            fa = cast(FamilyAllele, aa)
            assert set(fa.inheritance_in_members) == {inheritance}
