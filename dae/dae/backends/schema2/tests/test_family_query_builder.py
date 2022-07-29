# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pandas as pd
from dae.backends.schema2.base_query_builder import Dialect
from dae.backends.schema2.family_builder import FamilyQueryBuilder
from dae.variants.attributes import Role, Status, Sex


def test_get_all(resources_dir):
    dialect = Dialect()

    ped_df = pd.read_csv(resources_dir / "pedigree_table.csv")
    ped_df.role = ped_df.role.apply(Role)
    ped_df.sex = ped_df.sex.apply(Sex)
    ped_df.status = ped_df.status.apply(Status)

    family_query_builder = FamilyQueryBuilder(
        dialect=dialect,
        db="db",
        family_variant_table="family_alleles",
        summary_allele_table="summary_alleles",
        pedigree_table="pedigree",
        family_variant_schema={
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
        },
        summary_allele_schema={
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
        },
        table_properties=None,
        pedigree_schema={
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
        },
        pedigree_df=ped_df,
        gene_models=None,
        do_join_affected=False,
    )

    query = family_query_builder.build_query()
    assert query.startswith("SELECT")
