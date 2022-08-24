# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pandas as pd
import pytest
from dae.utils.regions import Region
from dae.backends.schema2.base_query_builder import Dialect
from dae.backends.schema2.family_builder import FamilyQueryBuilder
from dae.backends.schema2.summary_builder import SummaryQueryBuilder
from dae.variants.attributes import Role, Status, Sex


FAMILY_VARIANT_SCHEMA = {
    "bucket_index": "int",
    "summary_index": "int",
    "allele_index": "int",
    "family_index": "int",
    "family_id": "string",
    "is_denovo": "tinyint",
    "allele_in_sexes": "tinyint",
    "allele_in_statuses": "tinyint",
    "allele_in_roles": "int",
    "inheritance_in_members": "smallint",
    "allele_in_members": "array<string>",
    "family_variant_data": "string",
}

SUMMARY_ALLELE_SCHEMA = {
    "bucket_index": "int",
    "summary_index": "int",
    "allele_index": "int",
    "chromosome": "string",
    "position": "int",
    "end_position": "int",
    "effect_gene": "array<struct<\n  effect_gene_symbols:string,\n  \
effect_types:string\n>>",
    "variant_type": "tinyint",
    "transmission_type": "tinyint",
    "reference": "string",
    "af_allele_count": "int",
    "af_allele_freq": "float",
    "af_parents_called": "int",
    "af_parents_freq": "float",
    "summary_variant_data": "string",
}

PEDIGREE_SCHEMA = {
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

NO_PARTITIONING_PROPERTIES = {
    "region_length": 0,
    "chromosomes": [],
    "family_bin_size": 0,
    "coding_effect_types": [],
    "rare_boundary": 0
}


@pytest.fixture(scope="module")
def pedigree_df(resources_dir):
    ped_df = pd.read_csv(resources_dir / "pedigree_table.csv")
    ped_df.role = ped_df.role.apply(Role)
    ped_df.sex = ped_df.sex.apply(Sex)
    ped_df.status = ped_df.status.apply(Status)


@pytest.fixture()
def family_query_builder(pedigree_df):
    dialect = Dialect()

    return FamilyQueryBuilder(
        dialect=dialect,
        db="db",
        family_variant_table="family_alleles",
        summary_allele_table="summary_alleles",
        pedigree_table="pedigree",
        family_variant_schema=FAMILY_VARIANT_SCHEMA,
        summary_allele_schema=SUMMARY_ALLELE_SCHEMA,
        table_properties=NO_PARTITIONING_PROPERTIES,
        pedigree_schema=PEDIGREE_SCHEMA,
        pedigree_df=pedigree_df,
        gene_models=None,
        do_join_pedigree=False,
    )


@pytest.fixture()
def summary_query_builder(pedigree_df):
    dialect = Dialect()

    return SummaryQueryBuilder(
        dialect=dialect,
        db="db",
        family_variant_table="family_alleles",
        summary_allele_table="summary_alleles",
        pedigree_table="pedigree",
        family_variant_schema=FAMILY_VARIANT_SCHEMA,
        summary_allele_schema=SUMMARY_ALLELE_SCHEMA,
        table_properties=NO_PARTITIONING_PROPERTIES,
        pedigree_schema=PEDIGREE_SCHEMA,
        pedigree_df=pedigree_df,
        gene_models=None,
        do_join_affected=False,
    )


@pytest.fixture(params=["family", "summary"])
def query_builder(request, family_query_builder, summary_query_builder):
    if request.param == "family":
        return family_query_builder
    return summary_query_builder


def test_get_all(query_builder):
    query = query_builder.build_query()
    assert query.startswith("SELECT")


def test_limit(query_builder):
    query = query_builder.build_query(limit=100)
    assert "LIMIT 100" in query


def test_regions(query_builder):
    query = query_builder.build_query(regions=[Region("X", 5, 15)])
    assert "`chromosome` = 'X'" in query
    assert "5 <= `position`" in query
    assert "15 >= COALESCE(`end_position`, `position`)" in query
