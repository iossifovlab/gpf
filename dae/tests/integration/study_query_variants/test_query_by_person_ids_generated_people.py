# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

import pytest

from dae.utils.regions import Region
from dae.testing import setup_pedigree, setup_vcf, \
    vcf_study
from dae.testing.alla_import import alla_gpf
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData


@pytest.fixture(scope="module")
def imported_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"query_by_person_ids_{genotype_storage.storage_id}")
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
familyId personId dadId momId sex status role            generated
f1       mom1     0     0     2    -     mom             true
f1       prb1     dad1  mom1  1    1     maternal_cousin false
f1       unknown1 0     0     1    1     unknown         false
f1       dad1     0     0     1    -     dad             true
f2       mom2     0     0     2    -     mom             false
f2       prb2     dad2  mom2  1    1     prb             false
f2       dad2     0     0     1    -     dad             false
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT prb1 unknown1 mom2 dad2 prb2
chrA   1   .  A   C,G .    .      .    GT     0/1  0/0      0/0  0/0  0/1
        """)

    study = vcf_study(
        root_path,
        "vcf_with_generated_people", pathlib.Path(ped_path),
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
                }
            },
            "processing_config": {
                "include_reference": True
            }
        })
    return study


@pytest.mark.parametrize(
    "begin, end, person_ids, count",
    [
        (1, 1, None, 2),
        (1, 1, ["prb1"], 1),
        (1, 1, ["prb2"], 1),
        (1, 1, ["prb1", "prb2"], 2),
    ]
)
def test_query_by_person_ids_generated_people(
    imported_study: GenotypeData,
    begin: int,
    end: int,
    person_ids: Optional[list[str]],
    count: int
) -> None:
    region = Region("chrA", begin, end)
    vs = list(imported_study.query_variants(
        regions=[region],
        person_ids=person_ids,
        return_unknown=False,
        return_reference=False))

    assert len(vs) == count
