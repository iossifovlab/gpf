# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
from sqlglot import exp, parse_one
from sqlglot.executor import execute
from sqlglot.schema import ensure_schema

from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.query_variants.sql.schema2.sql_query_builder import (
    Db2Layout,
    RealAttrFilterType,
    SqlQueryBuilder,
)
from dae.testing import setup_pedigree
from dae.testing.t4c8_import import t4c8_genes, t4c8_genome
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance, Role, Sex
from dae.variants.core import Allele


@pytest.fixture()
def pedigree_schema_simple() -> dict[str, str]:
    schema: dict[str, str] = {
        "family_id": "string",
        "person_id": "string",
        "dad_id": "string",
        "mom_id": "string",
        "sex": "tinyint",
        "status": "tinyint",
        "role": "int",
        "sample_id": "string",
        "generated": "boolean",
        "layout": "string",
        "not_sequenced": "boolean",
        "tag_multiplex_family": "string",
        "tag_simplex_family": "string",
        "tag_quad_family": "string",
        "tag_family_type": "string",
        "tag_affected_prb_family": "string",
        "tag_affected_mom_family": "string",
        "tag_missing_dad_family": "string",
        "tag_control_family": "string",
        "tags": "string",
        "tag_missing_mom_family": "string",
        "tag_affected_dad_family": "string",
        "tag_nuclear_family": "string",
        "tag_trio_family": "string",
        "tag_affected_sib_family": "string",
        "tag_family_type_full": "string",
        "member_index": "string",
        "tag_male_prb_family": "string",
        "tag_female_prb_family": "string",
    }
    return schema


@pytest.fixture()
def summary_schema_simple() -> dict[str, str]:
    return {
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
        "tt": "float",
        "seen_as_denovo": "bool",
        "seen_in_status": "int8",
        "family_variants_count": "int32",
        "family_alleles_count": "int32",
        "summary_variant_data": "string",
    }


@pytest.fixture()
def family_schema_simple() -> dict[str, str]:
    return {
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


@pytest.fixture()
def db_layout_simple() -> Db2Layout:
    return Db2Layout(
        db="test_db",
        study="test_vcf",
        pedigree="test_vcf_pedigree",
        summary="test_vcf_summary",
        family="test_vcf_family",
        meta="test_vcf_meta",
    )


@pytest.fixture()
def families_simple(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "pedigree" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     2   2      prb
        """)
    return FamiliesLoader(ped_path).load()


@pytest.fixture()
def t4c8_gene_models(tmp_path: pathlib.Path) -> GeneModels:
    return t4c8_genes(tmp_path / "gene_models")


@pytest.fixture()
def t4c8_ref_genome(tmp_path: pathlib.Path) -> ReferenceGenome:
    return t4c8_genome(tmp_path / "genome")


@pytest.fixture()
def sql_query_builder_simple(
    db_layout_simple: Db2Layout,
    pedigree_schema_simple: dict[str, str],
    summary_schema_simple: dict[str, str],
    family_schema_simple: dict[str, str],
    families_simple: FamiliesData,
    t4c8_gene_models: GeneModels,
    t4c8_ref_genome: ReferenceGenome,
) -> SqlQueryBuilder:
    schema = SqlQueryBuilder.build_schema(
        pedigree_schema=pedigree_schema_simple,
        summary_schema=summary_schema_simple,
        family_schema=family_schema_simple,
    )
    return SqlQueryBuilder(
        db_layout_simple,
        schema=schema,
        partition_descriptor=None,
        families=families_simple,
        gene_models=t4c8_gene_models,
        reference_genome=t4c8_ref_genome,
    )


def test_summary_query_builder_simple(
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    query = sql_query_builder_simple.build_summary_variants_query()
    assert query
    assert len(query) == 1
    expr = parse_one(query[0])
    assert expr


@pytest.mark.parametrize(
    "gene,expected", [
        ("t4", "chr1:5-85"),
        ("c8", "chr1:100-205"),
    ],
)
def test_build_gene_regions_heuristic(
    sql_query_builder_simple: SqlQueryBuilder,
    gene: str,
    expected: str,
) -> None:
    genes = [gene]
    regions = None
    sql_query_builder_simple.GENE_REGIONS_HEURISTIC_EXTEND = 0
    result = sql_query_builder_simple.build_gene_regions(
        genes, regions,
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
    ],
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
    where = sql_query_builder_simple.build_regions_where(regions)
    query = f"SELECT * FROM summary_allele sa WHERE {where}"  # noqa: S608

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
    ],
)
def test_build_real_attr_where(
    sql_query_builder_simple: SqlQueryBuilder,
    real_attr_filter: RealAttrFilterType,
    is_frequency: bool,  # noqa: FBT001
    expected: int,
) -> None:
    tables = {
        "summary_allele": [
            {"af_allele_freq": 0.5},
            {"af_allele_freq": None},
            {"af_allele_freq": 50.0},

        ],
    }
    where = sql_query_builder_simple._build_real_attr_where(
        real_attr_filter, is_frequency=is_frequency,
    )
    if not is_frequency:
        assert where

    if where:
        query = f"SELECT * FROM summary_allele sa WHERE {where}"  # noqa: S608
    else:
        query = "SELECT * FROM summary_allele sa"

    result = execute(
        query,
        tables=tables)

    assert len(result) == expected


def test_build_ultra_rare_where(
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    tables = {
        "summary_allele": [
            {"af_allele_count": 1},
            {"af_allele_count": None},
            {"af_allele_count": 50},

        ],
    }
    where = sql_query_builder_simple._build_ultra_rare_where()
    query = f"SELECT * FROM summary_allele sa WHERE {where}"  # noqa: S608

    result = execute(
        query,
        tables=tables)

    assert len(result) == 2


def test_build_gene_query_where(
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    query = sql_query_builder_simple.build_summary_variants_query(
        genes=["t4"], effect_types=["missense"],
    )
    assert len(query) == 1
    print(query)
    expr = parse_one(query[0], read="duckdb")
    assert expr


def test_sqlglot_nested_schema_experiments() -> None:
    table_schema = {
        "test": {
            "a": "int64",
            "b": exp.DataType.Type.ARRAY,
            "c": exp.DataType.Type.STRUCT,
        },
    }
    schema = ensure_schema(table_schema)
    assert schema
    assert schema.column_names("test") == ["a", "b", "c"]


def test_sql_query_builder_effect_types(
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    effect_types = ["5'UTR", "3'UTR"]
    result = sql_query_builder_simple._build_effect_type_where(effect_types)
    assert result == "eg.effect_types in ('5''UTR','3''UTR')"


@pytest.mark.parametrize(
    "real_attr_filter,is_frequency,expected", [
        (
            [("tt", (None, 1.0))],
            True,
            "( sa.tt <= 1.0 OR sa.tt IS NULL )",
        ),
        (
            [("tt", (None, 1.0))],
            False,
            "( sa.tt <= 1.0 )",
        ),
        (
            [("tt", (0.0, 1.0))],
            True,
            "( sa.tt >= 0.0 AND sa.tt <= 1.0 )",
        ),
        (
            [("tt", (0.0, 1.0))],
            False,
            "( sa.tt >= 0.0 AND sa.tt <= 1.0 )",
        ),
        (
            [("tt", (0.0, None))],
            True,
            "( sa.tt >= 0.0 )",
        ),
        (
            [("tt", (0.0, None))],
            False,
            "( sa.tt >= 0.0 )",
        ),
        (
            [("tt", (None, None))],
            True,
            "",
        ),
        (
            [("tt", (None, None))],
            False,
            "( sa.tt IS NOT NULL )",
        ),
    ],
)
def test_sql_query_builder_real_attr_where(
    real_attr_filter: RealAttrFilterType,
    is_frequency: bool,  # noqa: FBT001
    expected: str,
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    result = sql_query_builder_simple._build_real_attr_where(
        real_attr_filter, is_frequency=is_frequency)  # type: ignore
    assert result == expected


@pytest.mark.parametrize(
    "sex_query,value,expected", [
        ("male", Sex.male.value, True),
        ("male", Sex.male.value | Sex.female.value, True),
        ("male", Sex.female.value | Sex.unspecified.value, False),
        ("female", Sex.male.value | Sex.female.value, True),
        ("female and not male", Sex.male.value | Sex.female.value, False),
        ("female and not male",
         Sex.unspecified.value | Sex.female.value, True),
    ],
)
def test_sex_query_duckdb(
    sex_query: str,
    value: int,
    expected: int,
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    res = sql_query_builder_simple.check_sexes_query_value(sex_query, value)
    assert res == expected


@pytest.mark.parametrize(
    "inheritance_query,value,expected", [
        (["denovo"], Inheritance.denovo.value, True),
        (["denovo", "mendelian"], Inheritance.denovo.value, False),
        (["denovo or mendelian"], Inheritance.denovo.value, True),
    ],
)
def test_inheritance_query_duckdb(
    inheritance_query: list[str],
    value: int,
    expected: int,
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    res = sql_query_builder_simple.check_inheritance_query_value(
        inheritance_query, value)
    assert res == expected


@pytest.mark.parametrize(
    "role_query,value,expected", [
        ("prb and not mom and not dad", Role.prb.value, True),
        ("prb and not mom and not dad", Role.sib.value, False),
        ("prb and not mom and not dad",
         Role.prb.value | Role.mom.value, False),
        ("prb and not mom and not dad",
         Role.prb.value | Role.dad.value, False),
        ("prb and not mom and not dad",
         Role.prb.value | Role.sib.value, True),
        ("(prb or sib) and (mom or dad)",
         Role.prb.value | Role.mom.value, True),
        ("(prb or sib) and (mom or dad)",
         Role.prb.value | Role.mom.value | Role.dad.value, True),
        ("(prb or sib) and (mom or dad)",
         Role.sib.value | Role.mom.value | Role.dad.value, True),
        ("(prb or sib) and (mom or dad)",
         Role.mom.value | Role.dad.value, False),
        ("not prb", Role.prb.value, False),
        ("not prb", Role.prb.value | Role.sib.value, False),
        ("not prb", Role.sib.value, True),
        ("not prb", Role.dad.value | Role.mom.value, True),
        ("prb and (mom or dad)", Role.prb.value | Role.mom.value, True),
        ("prb and (mom or dad)", Role.prb.value | Role.dad.value, True),
        ("prb and (mom or dad)",
         Role.prb.value | Role.sib.value | Role.dad.value, True),
        ("prb and (mom or dad)",
         Role.sib.value | Role.dad.value | Role.mom.value, False),
        ("prb",
         Role.not_role(Role.prb.value), False),
        ("prb",
         Role.not_role(Role.prb.value | Role.sib.value), False),
        ("mom",
         Role.not_role(Role.prb.value | Role.sib.value), True),
        ("(prb or sib) and not (mom or dad)",
         Role.prb.value | Role.sib.value, True),
        ("(prb or sib) and not (mom or dad)",
         Role.dad.value, False),
        ("(prb or sib) and not (mom or dad)",
         Role.dad.value | Role.mom.value, False),
        ("prb", Role.not_role(Role.dad.value | Role.mom.value), True),
        ("(prb and not sib) and (mom and not dad)",
         Role.prb.value | Role.mom.value, True),
    ],
)
def test_role_query_duckdb(
    role_query: str,
    value: int,
    expected: int,
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    res = sql_query_builder_simple.check_roles_query_value(role_query, value)
    assert res == expected


@pytest.mark.parametrize(
    "roles_query,expected", [
        ("prb", False),
        ("sib", False),
        ("prb or sib", False),
        ("prb and not (mom or dad)", True),
        ("sib and not (mom or dad)", True),
        ("prb and mom", False),
        ("prb and (mom or dad)", False),
        ("(prb and not sib) or (prb and sib)", False),
        ("((prb and not sib) or (prb and sib)) and (not mom and not dad)",
         True),
        ("( prb and not sib ) or ( prb and sib )", False),
    ],
)
def test_role_query_denovo_only(
    roles_query: str,
    expected: int,
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    res = sql_query_builder_simple.check_roles_denovo_only(roles_query)
    assert res == expected


@pytest.mark.parametrize(
    "inheritance_query,expected", [
        (["denovo"], True),
        (["mendelian"], False),
        (["missing"], False),
        (["denovo or mendelian"], False),
        (["denovo and not mendelian"], True),
        (["denovo or possible_denovo"], False),
        (["any(denovo,mendelian,missing,omission)"], False),
        (["not possible_denovo and not possible_omission"], False),
        (["any(denovo,mendelian,missing,omission)",
          "not possible_denovo and not possible_omission"], False),
    ],
)
def test_inheritance_query_denovo_only(
    inheritance_query: str,
    expected: int,
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    res = sql_query_builder_simple.check_inheritance_denovo_only(
        inheritance_query)
    assert res == expected


@pytest.mark.parametrize(
    "variant_types_query,value,expected", [
        ("ins or del", Allele.Type.small_deletion.value, True),
        ("ins or del", Allele.Type.small_insertion.value, True),
        ("ins or del",
         Allele.Type.small_insertion.value
         | Allele.Type.small_deletion.value, True),
        ("sub",
         Allele.Type.small_insertion.value
         | Allele.Type.small_deletion.value, False),
        ("sub or complex",
         Allele.Type.small_insertion.value
         | Allele.Type.small_deletion.value, False),
        ("sub or complex",
         Allele.Type.substitution.value
         | Allele.Type.small_deletion.value, True),
        ("sub or complex",
         Allele.Type.complex.value
         | Allele.Type.small_deletion.value, True),
        ("cnv+",
         Allele.Type.large_duplication.value
         | Allele.Type.large_deletion.value, True),
        ("cnv-",
         Allele.Type.large_duplication.value
         | Allele.Type.large_deletion.value, True),
        ("cnv-",
         Allele.Type.small_insertion.value
         | Allele.Type.small_deletion.value, False),
        ("CNV+",
         Allele.Type.small_insertion.value
         | Allele.Type.small_deletion.value, False),
    ],
)
def test_variant_types_query_duckdb(
    variant_types_query: str,
    value: int,
    expected: bool,  # noqa: FBT001
    sql_query_builder_simple: SqlQueryBuilder,
) -> None:
    res = sql_query_builder_simple.check_variant_types_value(
        variant_types_query, value)
    assert res == expected
