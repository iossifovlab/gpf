'''
Created on May 30, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

from builtins import str
import sys
import traceback

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

# from tqdm import tqdm

from variants.attributes import Role, Sex


def summary_parquet_schema():

    fields = [
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int64()),
        pa.field("reference", pa.string()),
        pa.field("alternative", pa.string()),
        pa.field("bucket_index", pa.int16()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int16()),
        pa.field("allele_count", pa.int16()),
        pa.field("variant_type", pa.int8()),
        pa.field("cshl_variant", pa.string()),
        pa.field("cshl_position", pa.int64()),
        # pa.field("cshl_length", pa.int32()),
        pa.field("effect_type", pa.string()),
        pa.field("effect_gene_genes", pa.list_(pa.string())),
        pa.field("effect_gene_types", pa.list_(pa.string())),
        pa.field("effect_details_transcript_ids", pa.list_(pa.string())),
        pa.field("effect_details_details", pa.list_(pa.string())),
        pa.field("af_parents_called_count", pa.int32()),
        pa.field("af_parents_called_percent", pa.float64()),
        pa.field("af_allele_count", pa.int32()),
        pa.field("af_allele_freq", pa.float64()),
        pa.field("frequency_type", pa.string()),
        # pa.field("ultra_rare", pa.bool_()),
    ]

    return pa.schema(fields)


def effect_gene_parquet_schema():
    fields = [
        pa.field("bucket_index", pa.int16()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int16()),
        pa.field("effect_gene_index", pa.int8()),
        pa.field("effect_type", pa.string()),
        pa.field("effect_gene", pa.string()),
    ]
    return pa.schema(fields)


def batch_from_data_dict(data, schema):
    batch_data = []
    for name in schema.names:
        assert name in data
        column = data[name]
        field = schema.field_by_name(name)
        batch_data.append(pa.array(column, type=field.type))
    batch = pa.RecordBatch.from_arrays(batch_data, schema.names)
    return batch


def table_from_data_dict(data, schema):
    batch = batch_from_data_dict(data, schema)
    return pa.Table.from_batches([batch])


def summary_batch(sum_df):
    schema = summary_parquet_schema()

    batch_data = []
    for name in schema.names:
        assert name in sum_df, name
        data = sum_df[name].values
        field = schema.field_by_name(name)
        batch_data.append(pa.array(data, type=field.type))

    batch = pa.RecordBatch.from_arrays(
        batch_data,
        schema.names)

    return batch


def family_parquet_schema():
    fields = [
        pa.field("bucket_index", pa.int16()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int8()),
        pa.field("family_variant_index", pa.int64()),
        pa.field("family_id", pa.string()),
        pa.field("genotype", pa.list_(pa.int8())),
        pa.field("inheritance_in_members", pa.list_(pa.int8())),
        pa.field("variant_in_members", pa.list_(pa.string())),
        pa.field("variant_in_roles", pa.list_(pa.int8())),
        pa.field("variant_in_sexes", pa.list_(pa.int8())),
    ]
    return pa.schema(fields)


def member_parquet_schema():
    fields = [
        pa.field("bucket_index", pa.int16()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int8()),
        pa.field("family_variant_index", pa.int64()),
        # pa.field("family_id", pa.string()),
        # pa.field("member_index", pa.int8()),
        # pa.field("member_id", pa.string()),

        # pa.field("member_inheritance", pa.int8()),
        pa.field("member_variant", pa.string()),
        # pa.field("member_role", pa.int8()),
        # pa.field("member_sex", pa.int8()),
    ]
    return pa.schema(fields)


def setup_family_batch_data():
    return {
        "chrom": [],
        "position": [],
        "family_id": [],
        "family_variant_index": [],
        "bucket_index": [],
        "summary_variant_index": [],
        "allele_index": [],
        "genotype": [],
        "inheritance_in_members": [],
        "variant_in_members": [],
        "variant_in_roles": [],
        "variant_in_sexes": [],
    }


def _family_allele_to_data(
        family_data, member_data, fv, fa,
        bucket_index, summary_index, family_index):
    family_data["chrom"].append(fa.chromosome)
    family_data["position"].append(fa.position)
    family_data["family_id"].append(fa.family_id)
    family_data["family_variant_index"].append(family_index)

    family_data["bucket_index"].append(bucket_index)
    family_data["summary_variant_index"].append(summary_index)
    family_data["allele_index"].append(fa.allele_index)
    family_data["genotype"].append(fv.gt_flatten())
    family_data["inheritance_in_members"].\
        append(
            np.asarray([
                i.value for i in fa.inheritance_in_members
            ], dtype=np.int8))

    family_data["variant_in_members"].append(
        [str(m)
            for m in fa.variant_in_members])

    if fa.is_reference_allele:
        family_data["variant_in_roles"].append(None)
        family_data["variant_in_sexes"].append(None)
    else:
        family_data["variant_in_roles"].append(
            [
                r.value for r in set(fa.variant_in_roles) if r is not None
            ])
        family_data["variant_in_sexes"].append(
            [
                s.value for s in set(fa.variant_in_sexes) if s is not None
            ])

    assert len(fa.inheritance_in_members) == len(fa.members_ids)
    assert len(fa.variant_in_members) == len(fa.members_ids)
    assert len(fa.variant_in_roles) == len(fa.members_ids)
    assert len(fa.variant_in_sexes) == len(fa.members_ids)

    def value_or_none(v):
        if v is None:
            return None
        return v.value

    for member_index, member_id in enumerate(fa.members_ids):
        # if fa.variant_in_members[member_index] is None:
        #     continue

        member_data["bucket_index"].append(bucket_index)
        member_data["summary_variant_index"].append(summary_index)
        member_data["allele_index"].append(fa.allele_index)
        member_data["family_variant_index"].append(family_index)
        # member_data["member_index"].append(member_index)

        # member_data["family_id"].append(fa.family_id)
        # member_data["member_id"].append(member_id)
        # member_data["member_inheritance"].append(
        #     fa.inheritance_in_members[member_index].value)
        member_data["member_variant"].append(
            fa.variant_in_members[member_index])
        # member_data["member_role"].append(
        #     value_or_none(fa.variant_in_roles[member_index])
        # )
        # member_data["member_sex"].append(
        #     value_or_none(fa.variant_in_sexes[member_index])
        # )


def variants_table(variants, bucket_index=1, batch_size=200000):
    family_schema = family_parquet_schema()
    family_data = setup_family_batch_data()
    member_schema = member_parquet_schema()
    member_data = {
        name: [] for name in member_schema.names
    }

    summary_schema = summary_parquet_schema()
    summary_data = {
        name: [] for name in summary_schema.names
    }

    effect_gene_schema = effect_gene_parquet_schema()
    effect_gene_data = {
        name: [] for name in effect_gene_schema.names
    }

    family_variant_index = 0

    for summary_variant_index, vs in enumerate(variants):
        summary_variant, family_variants = vs

        for sa in summary_variant.alleles:
            sa.attributes['bucket_index'] = bucket_index
            for name in summary_schema.names:
                summary_data[name].append(sa.get_attribute(name))
            if sa.is_reference_allele:
                continue
            for effect_gene_index, effect_gene in enumerate(sa.effects.genes):
                effect_gene_data["bucket_index"].append(bucket_index)
                effect_gene_data["summary_variant_index"].append(
                    summary_variant_index)
                effect_gene_data["allele_index"].append(sa.allele_index)
                effect_gene_data["effect_gene_index"].append(
                    effect_gene_index)
                effect_gene_data["effect_type"].append(effect_gene.effect)
                effect_gene_data["effect_gene"].append(effect_gene.symbol)

        for fv in family_variants:
            for allele in fv.alleles:
                _family_allele_to_data(
                    family_data, member_data, fv, allele,
                    bucket_index, summary_variant_index, family_variant_index)
                family_variant_index += 1

        if len(family_data['chrom']) >= batch_size:

            family_table = table_from_data_dict(
                family_data, family_schema)
            member_table = table_from_data_dict(
                member_data, member_schema
            )
            summary_table = table_from_data_dict(
                summary_data, summary_schema
            )
            effect_gene_table = table_from_data_dict(
                effect_gene_data, effect_gene_schema
            )
            effect_gene_data = {
                name: [] for name in effect_gene_schema.names
            }

            summary_data = {
                name: [] for name in summary_schema.names
            }
            family_data = setup_family_batch_data()
            member_data = {
                name: [] for name in member_schema.names
            }

            yield summary_table, effect_gene_table, family_table, member_table

    if len(family_data['chrom']) > 0:
        family_table = table_from_data_dict(
            family_data, family_schema)
        member_table = table_from_data_dict(
            member_data, member_schema
        )
        summary_table = table_from_data_dict(
            summary_data, summary_schema
        )
        effect_gene_table = table_from_data_dict(
            effect_gene_data, effect_gene_schema
        )

        yield summary_table, effect_gene_table, family_table, member_table


def save_variants_to_parquet(
        variants,
        summary_filename=None, effect_gene_filename=None,
        family_filename=None, member_filename=None,
        bucket_index=1, batch_size=100000):
    family_schema = family_parquet_schema()
    family_writer = pq.ParquetWriter(family_filename, family_schema)
    member_schema = member_parquet_schema()
    member_writer = pq.ParquetWriter(member_filename, member_schema)
    summary_schema = summary_parquet_schema()
    summary_writer = pq.ParquetWriter(summary_filename, summary_schema)
    effect_gene_schema = effect_gene_parquet_schema()
    effect_gene_writer = pq.ParquetWriter(
        effect_gene_filename, effect_gene_schema)
    try:
        for stable, etable, ftable, mtable in variants_table(
                variants, bucket_index, batch_size):
            assert ftable.schema == family_schema
            assert ftable.num_rows > 0
            family_writer.write_table(ftable)
            assert mtable.schema == member_schema
            assert mtable.num_rows > 0
            member_writer.write_table(mtable)

            assert stable.schema == summary_schema
            assert stable.num_rows > 0
            summary_writer.write_table(stable)
            assert etable.schema == effect_gene_schema
            assert etable.num_rows > 0
            effect_gene_writer.write_table(etable)

    except Exception as ex:
        print("unexpected error:", ex)
        traceback.print_exc(file=sys.stdout)
    finally:
        family_writer.close()
        member_writer.close()
        summary_writer.close()
        effect_gene_writer.close()


def pedigree_parquet_schema():
    fields = [
        pa.field("familyId", pa.string()),
        pa.field("personId", pa.string()),
        pa.field("dadId", pa.string()),
        pa.field("momId", pa.string()),
        pa.field("sex", pa.int8()),
        pa.field("status", pa.int8()),
        pa.field("role", pa.int32()),
        pa.field("sampleId", pa.string()),
        pa.field("familyIndex", pa.int32()),
        pa.field("personIndex", pa.int32()),
    ]

    return pa.schema(fields)


def save_ped_df_to_parquet(ped_df, filename):
    ped_df = ped_df.copy()
    ped_df.role = ped_df.role.apply(lambda r: r.value)
    ped_df.sex = ped_df.sex.apply(lambda s: s.value)

    table = pa.Table.from_pandas(ped_df, schema=pedigree_parquet_schema())
    pq.write_table(table, filename)


def read_ped_df_from_parquet(filename):
    ped_df = pd.read_parquet(filename, engine="pyarrow")
    ped_df.role = ped_df.role.apply(lambda v: Role(v))
    ped_df.sex = ped_df.sex.apply(lambda v: Sex(v))
    if 'layout' in ped_df:
        ped_df.layout = ped_df.layout.apply(lambda v: v.split(':')[-1])

    return ped_df
