# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from collections.abc import Callable

import pytest
from dae.genomic_resources.testing import (
    setup_pedigree,
    setup_vcf,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeDataGroup
from dae.testing.alla_import import alla_gpf
from dae.testing.import_helpers import (
    setup_dataset,
    vcf_study,
)


@pytest.fixture(scope="module")
def dataset(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeDataGroup:
    root_path = tmp_path_factory.mktemp(
        "test_dataset_query_by_person_set_collection")
    gpf_instance = alla_gpf(root_path, genotype_storage_factory(root_path))

    ped_path1 = setup_pedigree(
        root_path / "study_1" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
f2       mom2     0     0     2   1      mom
f2       dad2     0     0     1   1      dad
f2       ch2      dad2  mom2  2   2      prb
        """))

    vcf_path1 = setup_vcf(
        root_path / "study_1" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 dad2 ch2 mom2
chr1   1   .  A   C,G     .    .      .    GT     0/1  0/2  0/0 0/1  0/0 0/0
chr1   2   .  A   C     .    .      .    GT     0/0  0/1  0/0 0/1  0/0 0/1
        """)

    ped_path2 = setup_pedigree(
        root_path / "study_2" / "in.ped", textwrap.dedent("""
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       ch1      dad1  mom1  2   2      prb
f2       mom2     0     0     2   1      mom
f2       dad2     0     0     1   1      dad
f2       ch2      dad2  mom2  2   2      prb
        """))

    vcf_path2 = setup_vcf(
        root_path / "study_2" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 dad2 ch2 mom2
chr1   1   .  A   C,G   .    .      .    GT     0/1  0/2  0/0 0/0  0/0 0/0
chr1   2   .  A   C     .    .      .    GT     0/1  0/0  0/0 0/1  0/0 0/1
        """)

    study1 = vcf_study(
        root_path,
        "study_1", ped_path1, [vcf_path1],
        gpf_instance=gpf_instance)
    study2 = vcf_study(
        root_path,
        "study_2", ped_path2, [vcf_path2],
        gpf_instance=gpf_instance)

    (root_path / "dataset").mkdir(exist_ok=True)

    return setup_dataset(
        "ds1", gpf_instance, study1, study2,
        dataset_config_update=textwrap.dedent(f"""
            conf_dir: {root_path / "dataset "}
        """),
    )


@pytest.mark.parametrize(
    "unique_family_variants, count",
    [
        (False, 7),
        (True, 4),
    ],
)
def test_unique_family_variants(
    dataset: GenotypeDataGroup,
    unique_family_variants: bool,  # noqa: FBT001
    count: int,
) -> None:
    vs = list(dataset.query_variants(
        unique_family_variants=unique_family_variants))

    assert len(vs) == count
