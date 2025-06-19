# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.person_sets import PSCQuery
from dae.studies.study import GenotypeData
from dae.testing import (
    setup_pedigree,
    setup_vcf,
    vcf_study,
)
from dae.testing.foobar_import import foobar_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_partitions")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(
        root_path / "gpf_instance",
        genotype_storage,
    )

    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     2   1      sib
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1  m2   d2 p2
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1 0/0 0/0 0/0 0/0  # freq 1/8 = 12.5%, splice-site, g1
        foo    10  .  C   G   .    .      .    GT     0/0 0/1 0/1 0/0 0/0 0/0 0/0  # freq 1/8 = 12.5%, intron, g1
        bar    11  .  C   G   .    .      .    GT     1/0 0/0 0/0 0/1 1/1 1/1 1/1  # freq 5/8 = 62.5%, missense, g2
        bar    12  .  A   T   .    .      .    GT     0/0 1/0 1/0 0/0 0/1 0/1 0/1  # freq 3/8 = 37.5%, synonymous, g2
        bar    13  .  C   T   .    .      .    GT     0/0 1/0 1/0 1/0 0/1 0/0 0/0  # freq 2/8 = 25.0%, missense, g2
        """)  # noqa

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["foo", "bar"],
                "region_length": 100,
            },
            "family_bin": {
                "family_bin_size": 2,
            },
            "frequency_bin": {
                "rare_boundary": 30,
            },
            "coding_bin": {
                "coding_effect_types": "splice-site,missense,synonymous",
            },
        },
        "processing_config": {
            "vcf": {
                "chromosomes": ["foo", "bar"],
                "region_length": 8,
            },
        },
    }

    return vcf_study(
        root_path,
        "test_partitions", ped_path, [vcf_path],
        gpf_instance,
        project_config_update=project_config_update)


@pytest.mark.parametrize(
    "family_ids,count",
    [
        (None, 8),
        (["f1"], 5),
        (["f2"], 3),
    ],
)
def test_query_family_id(
    family_ids: list[str] | None, count: int,
    imported_study: GenotypeData,
) -> None:
    vs = list(imported_study.query_variants(family_ids=family_ids))
    assert len(vs) == count


@pytest.mark.parametrize(
    "person_ids,count",
    [
        (None, 8),
        (["m1"], 2),
        (["d1"], 3),
        (["p1"], 4),
        (["s1"], 2),
        (["m2"], 3),
        (["d2"], 2),
        (["p2"], 2),
    ],
)
def test_query_person_id(
    person_ids: list[str] | None, count: int, imported_study: GenotypeData,
) -> None:
    vs = list(imported_study.query_variants(person_ids=person_ids))
    assert len(vs) == count


@pytest.mark.parametrize(
    "region,family_count,summary_count",
    [
        (Region("foo", 1, 20), 2, 2),
        (Region("bar", 1, 20), 6, 3),
    ],
)
def test_query_region(
    region: Region, family_count: int, summary_count: int,
    imported_study: GenotypeData,
) -> None:
    assert len(list(imported_study.
                    query_variants(regions=[region]))) == family_count

    assert len(list(imported_study.
                    query_summary_variants(regions=[region]))) == summary_count


def test_query_ultra_rare(imported_study: GenotypeData) -> None:
    assert len(list(
        imported_study.query_summary_variants(ultra_rare=True))) == 2
    assert len(list(imported_study.query_variants(ultra_rare=True))) == 2


@pytest.mark.parametrize(
    "effect,family_count,summary_count",
    [
        (None, 8, 5),
        (["missense"], 4, 2),
        (["intron"], 1, 1),
        (["missense", "intron"], 5, 3),
    ],
)
def test_query_effect(
    effect: list[str] | None,
    family_count: int, summary_count: int,
    imported_study: GenotypeData,
) -> None:
    assert len(list(imported_study.
                    query_summary_variants(effect_types=effect))) == \
        summary_count

    assert len(list(imported_study.
                    query_variants(effect_types=effect))) == family_count


def test_query_complex(imported_study: GenotypeData) -> None:
    vs = list(
        imported_study.
        query_variants(
            effect_types=["noStart"],
            person_ids=["s1"],
            frequency_filter=[("af_allele_freq", (10, 27))],
            regions=[Region("bar", 3, 17)],
            genes=["g2"],
        ),
    )
    assert len(vs) == 1


def test_query_pedigree_fields(imported_study: GenotypeData) -> None:
    assert len(list(
        imported_study.query_variants(
            person_set_collection=PSCQuery(
                "status", {"affected", "unaffected", "unspecified"})))) == 8


def test_af_parent_count(imported_study: GenotypeData) -> None:
    for v in imported_study.query_variants():
        assert v.get_attribute("af_parents_called_count") == [4]


def test_query_denovo(imported_study: GenotypeData) -> None:
    assert len(list(
        imported_study.query_variants(inheritance=["denovo"]))) == 0


def test_wdae_get_all_from_genotype_browser(
    imported_study: GenotypeData,
) -> None:
    res = list(imported_study.query_variants(
        effect_types=["3'UTR", "3'UTR-intron", "5'UTR", "5'UTR-intron",
                      "frame-shift", "intergenic", "intron", "missense",
                      "no-frame-shift", "no-frame-shift-newStop", "noEnd",
                      "noStart", "non-coding", "non-coding-intron", "nonsense",
                      "splice-site", "synonymous", "CDS", "CNV+", "CNV-"],
        inheritance=["not possible_denovo and not possible_omission",
                     "any([denovo,mendelian,missing,omission])"],
        real_attr_filter=[],
        study_filters=["test_partitions"],
        inheritanceTypeFilter=[],
        studyTypes=["we", "wg", "tg"],
        studyFilters=[],
        datasetId="test_partitions",
        unique_family_variants=False))
    assert len(res) == 8
