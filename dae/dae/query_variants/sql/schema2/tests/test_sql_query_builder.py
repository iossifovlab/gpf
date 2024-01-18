# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from sqlglot import parse_one, exp
from sqlglot.executor import execute
from sqlglot.schema import ensure_schema

from dae.utils.regions import Region
from dae.genomic_resources.gene_models import GeneModels
from dae.query_variants.sql.schema2.sql_query_builder import Db2Layout
from dae.testing import setup_pedigree
from dae.testing.t4c8_import import t4c8_genes
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader

from dae.query_variants.sql.schema2.sql_query_builder import \
    SqlQueryBuilder, \
    RealAttrFilterType


def test_summary_query_builder() -> None:
    sql = """
WITH summary AS (
SELECT *
  FROM
    summary_table AS sa
  WHERE
    ( sa.region_bin IN ('chr14_0')) AND
    ( ( sa.chromosome = 'chr14' AND
      ((sa.position >= 21365194 AND sa.position <= 21457298) OR
       (COALESCE(sa.end_position, -1) >= 21365194 AND
        COALESCE(sa.end_position, -1) <= 21457298) OR
       (21365194 >= sa.position AND
        21457298 <= COALESCE(sa.end_position, -1)))
    ) ) AND
    ( sa.allele_index > 0 )
)
SELECT count(*)
FROM summary
CROSS JOIN
    (SELECT UNNEST (summary.effect_gene) as eg)
WHERE
    eg.effect_gene_symbols in ('CHD8');
    """
    expr = parse_one(sql)
    assert expr


@pytest.fixture
def pedigree_schema_simple() -> dict[str, str]:
    schema: dict[str, str] = {}
    return schema


@pytest.fixture
def summary_schema_simple() -> dict[str, str]:
    schema = {
        "bucket_index": "int32",
        "summary_index": "int32",
        "allele_index": "int32",
        "chromosome": "string",
        "position": "int32",
        "end_position": "int32",
        "effect_gene":
        "list<item: struct<effect_gene_symbols:string, effect_types:string>>",
        "variant_type": "int8",
        "transmission_type": "int8",
        "reference": "string",
        "af_allele_count": "int32",
        "af_allele_freq": "float",
        "af_parents_called_count": "int32",
        "af_parents_called_percent": "float",
        "seen_as_denovo": "bool",
        "seen_in_status": "int8",
        "family_variants_count": "int32",
        "family_alleles_count": "int32",
        "summary_variant_data": "string",
    }
    return schema


@pytest.fixture
def family_schema_simple() -> dict[str, str]:
    schema = {
        "bucket_index": "int32",
        "summary_index": "int32",
        "allele_index": "int32",
        "family_index": "int32",
        "family_id": "string",
        "is_denovo": "int8",
        "allele_in_sexes": "int8",
        "allele_in_statuses": "int8",
        "allele_in_roles": "int32",
        "inheritance_in_members": "int16",
        "allele_in_members": "list<item: string>",
        "family_variant_data": "string",
    }
    return schema


@pytest.fixture
def db_layout_simple(
    pedigree_schema_simple: dict[str, str],
    summary_schema_simple: dict[str, str],
    family_schema_simple: dict[str, str],
) -> Db2Layout:
    db_layout = Db2Layout(
        db="test_db",
        study="test_vcf",
        pedigree="test_vcf_pedigree",
        pedigree_schema=pedigree_schema_simple,
        summary="test_vcf_summary",
        summary_schema=summary_schema_simple,
        family="test_vcf_family",
        family_schema=family_schema_simple,
        meta="test_vcf_meta",
    )
    return db_layout


@pytest.fixture
def families_simple(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "pedigree" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     2   2      prb
        """)
    families = FamiliesLoader(ped_path).load()
    return families


@pytest.fixture
def t4c8_gene_models(tmp_path: pathlib.Path) -> GeneModels:
    return t4c8_genes(tmp_path / "gene_models")


@pytest.fixture
def sql_query_builder_simple(
    db_layout_simple: Db2Layout,
    families_simple: FamiliesData,
    t4c8_gene_models: GeneModels,
) -> SqlQueryBuilder:
    sql_query_builder = SqlQueryBuilder(
        db_layout_simple,
        None,
        families_simple,
        t4c8_gene_models,
    )
    return sql_query_builder


def test_summary_query_builder_simple(
    sql_query_builder_simple: SqlQueryBuilder
) -> None:
    query = sql_query_builder_simple.build_summary_variants_query()
    assert query
    expr = parse_one(query)
    assert expr


@pytest.mark.parametrize(
    "gene,expected", [
        ("t4", "chr1:4-86"),
        ("c8", "chr1:99-206"),
    ]
)
def test_build_gene_regions_heuristic(
    sql_query_builder_simple: SqlQueryBuilder,
    gene: str,
    expected: str,
) -> None:
    genes = [gene]
    regions = None
    sql_query_builder_simple.GENE_REGIONS_HEURISTIC_EXTEND = 2
    result = sql_query_builder_simple._build_gene_regions_heuristic(
        genes, regions
    )
    assert result is not None
    assert len(result) == 1

    reg = result[0]
    assert str(reg) == expected


@pytest.mark.parametrize(
    "regions,expected", [
        ([Region("chr1", 10, 20)], 1),
        ([Region("chr1", 12, 20)], 1),
        ([Region("chr1", 5, 12)], 1),
        ([Region("chr1", 49, 51)], 1),
        ([Region("chr1", 50, 51)], 1),
        ([Region("chr1", 49, 50)], 1),
        ([Region("chr1", 10, 30)], 2),
        ([Region("chr1", 10, 30), Region("chr1", 40, 50)], 3),
    ]
)
def test_build_regions_where(
    sql_query_builder_simple: SqlQueryBuilder,
    regions: list[Region],
    expected: int,
) -> None:
    tables = {
        "summary_allele": [
            {"chromosome": "chr1", "position": 11, "end_position": 13},
            {"chromosome": "chr1", "position": 30, "end_position": 33},
            {"chromosome": "chr1", "position": 50, "end_position": None},
        ],
    }
    where = sql_query_builder_simple._build_regions_where(regions)
    query = f"SELECT * FROM summary_allele sa WHERE {where}"

    result = execute(
        query,
        tables=tables)

    assert len(result) == expected


@pytest.mark.parametrize(
    "real_attr_filter,is_frequency,expected", [
        ([("af_allele_freq", (0.0, 1.0))], True, 1),
        ([("af_allele_freq", (None, 1.0))], True, 2),
        ([("af_allele_freq", (0.5, None))], True, 2),
        ([("af_allele_freq", (None, None))], True, 3),

        ([("af_allele_freq", (0.0, 1.0))], False, 1),
        ([("af_allele_freq", (None, 1.0))], False, 1),
        ([("af_allele_freq", (0.5, None))], False, 2),
        ([("af_allele_freq", (None, None))], False, 2),
    ]
)
def test_build_real_attr_where(
    sql_query_builder_simple: SqlQueryBuilder,
    real_attr_filter: RealAttrFilterType,
    is_frequency: bool,
    expected: int,
) -> None:
    tables = {
        "summary_allele": [
            {"af_allele_freq": 0.5, },
            {"af_allele_freq": None, },
            {"af_allele_freq": 50.0, },

        ],
    }
    where = sql_query_builder_simple._build_real_attr_where(
        real_attr_filter, is_frequency
    )
    if not is_frequency:
        assert where

    if where:
        query = f"SELECT * FROM summary_allele sa WHERE {where}"
    else:
        query = "SELECT * FROM summary_allele sa"

    result = execute(
        query,
        tables=tables)

    assert len(result) == expected


def test_build_ultra_rare_where(
    sql_query_builder_simple: SqlQueryBuilder
) -> None:
    tables = {
        "summary_allele": [
            {"af_allele_count": 1, },
            {"af_allele_count": None, },
            {"af_allele_count": 50, },

        ],
    }
    where = sql_query_builder_simple._build_ultra_rare_where()
    query = f"SELECT * FROM summary_allele sa WHERE {where}"

    result = execute(
        query,
        tables=tables)

    assert len(result) == 2


def test_build_gene_query_where(
    sql_query_builder_simple: SqlQueryBuilder
) -> None:
    query = sql_query_builder_simple.build_summary_variants_query(
        genes=["t4"], effect_types=["missense"]
    )
    print(query)

    expr = parse_one(query, read="duckdb")
    assert expr

    # tables = {
    #     "test_vcf_summary": [
    #         {
    #             "bucket_index": 1,
    #             "summary_index": 1,
    #             "allele_index": 1,
    #             "chromosome": "chr1",
    #             "position": 10,
    #             "end_position": None,
    #             "effect_gene": [
    #                 {"effect_gene_symbols": "t4", "effect_types": "missense"}
    #             ],
    #             "summary_variant_data": "summary_1",
    #         },

    #         {
    #             "bucket_index": 1,
    #             "summary_index": 2,
    #             "allele_index": 1,
    #             "chromosome": "chr1",
    #             "position": 120,
    #             "end_position": None,
    #             "effect_gene": [
    #                 {"effect_gene_symbols": "c8", "effect_types": "missense"}
    #             ],
    #             "summary_variant_data": "summary_2",
    #         },
    #     ],
    # }
    # result = execute(
    #     query,
    #     read="duckdb",
    #     tables=tables)

    # assert len(result) == 1


def test_sqlglot_nested_schema_experiments() -> None:
    table_schema = {
        "test": {
            "a": "int64",
            "b": exp.DataType.Type.ARRAY,
            "c": exp.DataType.Type.STRUCT,
        }
    }
    schema = ensure_schema(table_schema)
    assert schema
    assert schema.column_names("test") == ["a", "b", "c"]

    # assert schema.get_column_type("test", "a") == exp.DataType.Type.BIGINT
    # assert schema.get_column_type("test", "b") == exp.DataType.Type.ARRAY
