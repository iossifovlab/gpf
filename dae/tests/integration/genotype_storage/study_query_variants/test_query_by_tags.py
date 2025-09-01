# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.query_variants.sql.schema2.sql_query_builder import TagsQuery
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_query_by_family_tags")
    genotype_storage = genotype_storage_factory(root_path)
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
        f2        ch2       dad2   mom2   1    2       prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1 dad2 mom2 ch2
chrA   1   .  A   G     .    .      .    GT     0/0  0/1  0/1 0/0  0/0  0/0
chrA   2   .  A   G     .    .      .    GT     0/0  0/0  0/0 1/1  0/0  1/1
        """)

    return vcf_study(
        root_path,
        "test_query_by_family_tags", ped_path, [vcf_path],
        gpf_instance=gpf_instance)


@pytest.mark.parametrize(
    "selected_family_tags,deselected_family_tags,tags_or_mode,count",
    [
        (["tag_male_prb_family"], [], False, 1),
        (["tag_female_prb_family"], [], False, 1),
        ([], ["tag_male_prb_family"], False, 1),
        ([], ["tag_female_prb_family"], False, 1),
        (["tag_male_prb_family"], ["tag_female_prb_family"], False, 1),
        (["tag_male_prb_family"], ["tag_female_prb_family"], True, 1),
        (["tag_male_prb_family", "tag_female_prb_family"], [], True, 2),
        (["tag_male_prb_family", "tag_female_prb_family"], [], False, 0),
        ([], ["tag_male_prb_family", "tag_female_prb_family"], True, 2),
        ([], ["tag_male_prb_family", "tag_female_prb_family"], False, 0),
    ],
)
def test_query_by_family_ids(
        imported_study: GenotypeData,
        selected_family_tags: list[str],
        deselected_family_tags: list[str],
        tags_or_mode: bool,  # noqa: FBT001
        count: int,
) -> None:
    vs = list(imported_study.query_variants(
        tags_query=TagsQuery(
            selected_family_tags=selected_family_tags,
            deselected_family_tags=deselected_family_tags,
            tags_or_mode=tags_or_mode,
        ),
    ))
    assert len(vs) == count
