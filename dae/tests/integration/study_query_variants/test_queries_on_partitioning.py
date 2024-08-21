# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import pytest

from dae.duckdb_storage.duckdb2_variants import DuckDb2Variants
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.query_variants.sql.schema2.sql_query_builder import (
    SqlQueryBuilder,
)
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def study_2(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"study_2_{genotype_storage.storage_id}")
    t4c8_instance = t4c8_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "study_2" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_2" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS  ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   4    .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/1  0/2  0/2
chr1   54   .  T   C    .    .      .    GT     0/1  0/1  0/1 0/1  0/0  0/1
chr1   90   .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/1  0/2  0/1
chr1   100  .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/2  0/2  0/0
chr1   119  .  A   G,C  .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
chr1   122  .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/2  0/2  0/2
        """)

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
            "frequency_bin": {
                "rare_boundary": 25.0,
            },
            "coding_bin": {
                "coding_effect_types": [
                    "frame-shift",
                    "noStart",
                    "missense",
                    "synonymous",
                ],
            },
            "family_bin": {
                "family_bin_size": 2,
            },
        },
    }

    return vcf_study(
        root_path,
        "study_2", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
    )


@pytest.mark.skip("we have no abstract query builder interace")
@pytest.mark.parametrize("params, coding_bin", [
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["synonymous"]}, 1),
    ({"effect_types": ["intergenic"]}, None),
    ({"effect_types": ["intergenic", "synonymous"]}, None),
    ({}, None),
])
def test_coding_bin_heuristics_query(
    params: dict[str, Any],
    coding_bin: int | None,
    query_builder: SqlQueryBuilder,
) -> None:
    assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
    queries = query_builder.build_summary_variants_query(**params)
    assert queries is not None
    assert len(queries) > 0
    query = queries[0]

    if coding_bin is None:
        assert "coding_bin" not in query
    else:
        assert f"sa.coding_bin = {coding_bin}" in query


@pytest.mark.skip("we have no abstract query builder interace")
@pytest.mark.parametrize("params, region_bins", [
    ({"regions": [Region("chr1", 2, 20)]}, ["chr1_0"]),
    ({"regions": [Region("chr1", 2, 120)]}, ["chr1_0", "chr1_1"]),
    ({"regions": [Region("chr1")]}, ["chr1_0", "chr1_1", "chr1_2"]),
    ({"regions": [Region("chr1", 105)]}, ["chr1_1", "chr1_2"]),
    ({"regions": [Region("chr1", None, 105)]}, ["chr1_0", "chr1_1"]),
])
def test_region_bin_heuristics_query(
    params: dict[str, Any],
    region_bins: list[str] | None,
    query_builder: SqlQueryBuilder,
) -> None:
    assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
    queries = query_builder.build_summary_variants_query(**params)
    assert queries is not None
    assert len(queries) > 0
    query = queries[0]

    if region_bins is None:
        assert "region_bin" not in query
    else:
        assert "sa.region_bin" in query
        for region_bin in region_bins:
            assert f"'{region_bin}'" in query


@pytest.mark.skip("we have no abstract query builder interace")
@pytest.mark.parametrize("params, frequency_bins", [
    ({"ultra_rare": True}, "(0, 1)"),
    ({"ultra_rare": False}, None),
    ({}, None),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, "(0, 1, 2)"),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, "(0, 1, 2)"),
    ({"frequency_filter": [("af_allele_freq", (None, 25.1))]}, None),
])
def test_frequency_bin_heuristics_query(
    params: dict[str, Any],
    frequency_bins: str | None,
    query_builder: SqlQueryBuilder,
) -> None:
    assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
    queries = query_builder.build_summary_variants_query(**params)
    assert queries is not None
    assert len(queries) > 0
    query = queries[0]

    if frequency_bins is None:
        assert "frequency_bin" not in query
    else:
        assert "sa.frequency_bin" in query
        assert f"sa.frequency_bin IN {frequency_bins}" in query


@pytest.mark.skip("we have no abstract query builder interace")
@pytest.mark.parametrize("params, coding_bin", [
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["synonymous"]}, 1),
    ({"effect_types": ["intergenic"]}, None),
    ({"effect_types": ["intergenic", "synonymous"]}, None),
    ({}, None),
])
def test_coding_bin_heuristics_family_query(
    params: dict[str, Any],
    coding_bin: int | None,
    query_builder: SqlQueryBuilder,
) -> None:
    assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
    queries = query_builder.build_family_variants_query(**params)
    assert queries is not None
    assert len(queries) > 0
    query = queries[0]

    if coding_bin is None:
        assert "coding_bin" not in query
    else:
        assert f"sa.coding_bin = {coding_bin}" in query
        assert f"fa.coding_bin = {coding_bin}" in query


@pytest.mark.skip("we have no abstract query builder interace")
@pytest.mark.parametrize("params, count, region_bins", [
    ({"regions": [Region("chr1", 2, 20)]}, 1, ["chr1_0"]),
    ({"regions": [Region("chr1", 2, 120)]}, 1, ["chr1_0", "chr1_1"]),
    ({"regions": [Region("chr1")]}, 1, ["chr1_0", "chr1_1", "chr1_2"]),
    ({"regions": [Region("chr1", 105)]}, 1, ["chr1_1", "chr1_2"]),
    ({"regions": [Region("chr1", None, 105)]}, 1, ["chr1_0", "chr1_1"]),
    ({"regions": None}, 3, ["chr1_0"]),
])
def test_region_bin_heuristics_family_query(
    params: dict[str, Any],
    count: int,
    region_bins: list[str],
    query_builder: SqlQueryBuilder,
) -> None:
    assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
    queries = query_builder.build_family_variants_query(**params)
    assert queries is not None
    assert len(queries) == count
    query = queries[0]

    assert "sa.region_bin" in query
    assert "fa.region_bin" in query
    for region_bin in region_bins:
        assert f"'{region_bin}'" in query


@pytest.mark.skip("we have no abstract query builder interace")
def test_region_bin_heuristics_batched_query(
    query_builder: SqlQueryBuilder,
) -> None:

    queries = query_builder.build_family_variants_query()

    assert queries is not None
    assert len(queries) == 3
    for query in queries:
        assert "sa.region_bin" in query
        assert "fa.region_bin" in query


@pytest.mark.skip("we have no abstract query builder interace")
@pytest.mark.parametrize("params, frequency_bins", [
    ({"ultra_rare": True}, "(0, 1)"),
    ({"ultra_rare": False}, None),
    ({}, None),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, "(0, 1, 2)"),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, "(0, 1, 2)"),
    ({"frequency_filter": [("af_allele_freq", (None, 25.1))]}, None),
])
def test_frequency_bin_heuristics_family_query(
    params: dict[str, Any],
    frequency_bins: str | None,
    query_builder: SqlQueryBuilder,
) -> None:
    assert query_builder.GENE_REGIONS_HEURISTIC_EXTEND == 0
    queries = query_builder.build_family_variants_query(**params)
    assert queries is not None
    assert len(queries) > 0
    query = queries[0]

    if frequency_bins is None:
        assert "frequency_bin" not in query
    else:
        assert "sa.frequency_bin" in query
        assert "fa.frequency_bin" in query
        assert f"fa.frequency_bin IN {frequency_bins}" in query


def test_variants_simple(study_2: GenotypeData) -> None:
    svs = list(study_2.query_summary_variants())
    assert len(svs) == 6

    fvs = list(study_2.query_variants())
    assert len(fvs) == 12


@pytest.mark.parametrize("params, count", [
    ({"genes": ["t4"]}, 2),
    ({"genes": ["c8"]}, 5),
    ({"effect_types": ["missense"]}, 2),
    ({"effect_types": ["synonymous"]}, 4),
    ({"regions": [Region("chr1")]}, 12),
    ({"regions": [Region("chr1", None, 55)]}, 4),
    ({"regions": [Region("chr1", 55, None)]}, 8),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 2),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 12),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, 9),
    ({"frequency_filter": [("af_allele_freq", (25.0, None))]}, 12),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 12),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 12),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 8),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
    ({"ultra_rare": True}, 2),
])
def test_query_family_variants_counting(
    params: dict[str, Any],
    count: int,
    study_2: GenotypeData,
) -> None:
    fvs = list(study_2.query_variants(**params))
    assert len(fvs) == count


@pytest.mark.parametrize("params, count", [
    ({"genes": ["t4"]}, 1),
    ({"genes": ["c8"]}, 3),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["synonymous"]}, 3),
    ({"regions": [Region("chr1")]}, 6),
    ({"regions": [Region("chr1", None, 55)]}, 2),
    ({"regions": [Region("chr1", 55, None)]}, 4),
    ({"frequency_filter": [("af_allele_freq", (None, 15.0))]}, 2),
    ({"frequency_filter": [("af_allele_freq", (15.0, None))]}, 6),
    ({"frequency_filter": [("af_allele_freq", (None, 25.0))]}, 5),
    ({"frequency_filter": [("af_allele_freq", (25.0, None))]}, 6),
    ({"real_attr_filter": [("af_allele_count", (None, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (1, None))]}, 6),
    ({"real_attr_filter": [("af_allele_count", (1, 1))]}, 2),
    ({"real_attr_filter": [("af_allele_count", (2, None))]}, 6),
    ({"real_attr_filter": [("af_allele_count", (2, 2))]}, 4),
    ({"limit": 1}, 1),
    ({"limit": 2}, 2),
    ({"ultra_rare": True}, 2),
])
def test_query_summary_variants_counting(
    params: dict[str, Any],
    count: int,
    study_2: GenotypeData,
) -> None:
    svs = list(study_2.query_summary_variants(**params))
    assert len(svs) == count


@pytest.mark.parametrize("skip,params, count", [
    (False, {}, 12),
    (True, {}, 16),
    (True, {"roles": "prb"}, 9),
    (True, {"roles": "not prb"}, 7),
    (True, {"roles": "mom and not prb"}, 5),
    (True, {"roles": "mom and dad and not prb"}, 3),
    (True, {"roles": "prb and not mom and not dad"}, 0),
])
def test_query_family_variants_by_role(
    skip: bool,  # noqa: FBT001
    params: dict[str, Any],
    count: int,
    study_2: GenotypeData,
) -> None:
    fvs = list(study_2.query_variants(
        skip_inmemory_filterng=skip,
        **params))
    assert len(fvs) == count


@pytest.mark.parametrize("skip,params, count", [
    (False, {}, 12),
    (True, {}, 16),
    (True, {"sexes": "M"}, 11),
    (True, {"sexes": "M and not F"}, 2),
    (True, {"sexes": "female and not male"}, 5),
])
def test_query_family_variants_by_sex(
    skip: bool,  # noqa: FBT001
    params: dict[str, Any],
    count: int,
    duckdb2_variants: DuckDb2Variants,
) -> None:
    fvs = list(duckdb2_variants.query_variants(
        skip_inmemory_filterng=skip,
        **params,
    ))
    assert len(fvs) == count


@pytest.mark.parametrize("skip,params, count", [
    (False, {}, 12),
    (True, {}, 16),
    (True, {"inheritance": ["missing"]}, 7),
    (True, {"inheritance": ["mendelian"]}, 9),
    (True, {"inheritance": ["denovo"]}, 0),
    (False, {"inheritance": ["mendelian or missing"]}, 12),
    (True, {"inheritance": ["mendelian or missing"]}, 16),
    (True, {"inheritance": ["mendelian and missing"]}, 0),
])
def test_query_family_variants_by_inheritance(
    skip: bool,  # noqa: FBT001
    params: dict[str, Any],
    count: int,
    study_2: GenotypeData,
) -> None:
    fvs = list(study_2.query_variants(
        skip_inmemory_filterng=skip,
        **params,
    ))
    assert len(fvs) == count


@pytest.mark.skip("we have no abstract query builder interace")
@pytest.mark.parametrize(
    "params,expected", [
        (
            {
                "roles": "( prb and not sib ) or ( prb and sib )",
                "inheritance": [
                    "not possible_denovo and not possible_omission",
                    "any(denovo,mendelian,missing,omission)",
                ],
                "ultra_rare": True,
            },
            ["0", "1"],
        ),
        (
            {
                "roles": "( prb and not sib ) or ( prb and sib )",
                "inheritance": [
                    "not possible_denovo and not possible_omission",
                    "any(denovo,mendelian,missing,omission)",
                ],
                "ultra_rare": False,
                "frequency_filter": [("af_allele_freq", (None, 1.0))],
            },
            ["0", "1", "2"],
        ),
    ],
)
def test_calc_frequency_bin_heuristics(
    params: dict[str, Any],
    expected: list[str],
    query_builder: SqlQueryBuilder,
) -> None:
    frequency_bins = query_builder.calc_frequency_bins(**params)
    assert frequency_bins == expected


@pytest.mark.parametrize("params, count", [
    ({}, 12),
    ({"variant_type": "sub"}, 10),
    ({"variant_type": "ins"}, 5),
    ({"variant_type": "del"}, 0),
])
def test_query_family_variants_by_variant_type(
    params: dict[str, Any],
    count: int,
    study_2: GenotypeData,
) -> None:
    fvs = list(study_2.query_variants(**params))
    assert len(fvs) == count


@pytest.mark.parametrize("skip, params, count", [
    (False, {}, 12),
    (True, {}, 16),
    (True, {"person_ids": ["ch3"]}, 5),
    (True, {"person_ids": ["ch3"], "family_ids": ["f1.1"]}, 0),
    (True, {"person_ids": ["ch3"], "family_ids": ["f1.3"]}, 5),
    (False, {"family_ids": ["f1.1"]}, 6),
    (True, {"family_ids": ["f1.1"]}, 7),
    (True, {"family_ids": ["f1.1"], "person_ids": ["ch1"]}, 4),
])
def test_query_family_variants_by_family_and_person_ids(
    skip: bool,  # noqa: FBT001
    params: dict[str, Any],
    count: int,
    study_2: GenotypeData,
) -> None:
    fvs = list(study_2.query_variants(
        skip_inmemory_filterng=skip,
        **params,
    ))
    assert len(fvs) == count
