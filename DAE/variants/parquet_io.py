'''
Created on May 30, 2018

@author: lubo
'''
from __future__ import print_function
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from variants.attributes import Inheritance


def summary_parquet_schema():
    effect_gene = pa.struct([
        pa.field("gene", pa.string()),
        pa.field("type", pa.string())
    ])

    assert effect_gene is not None

    effect_details = pa.struct([
        pa.field("transcript_id", pa.string()),
        pa.field("detail", pa.string())
    ])
    assert effect_details is not None

    fields = [
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int64()),
        pa.field("reference", pa.string()),
        pa.field("alternative", pa.string()),
        pa.field("var_index", pa.int64()),
        pa.field("split_from_multi_allelic", pa.bool_()),
        pa.field("allele_index", pa.int8()),
        pa.field("effect_type", pa.string()),
        pa.field("effect_gene", pa.list_(effect_gene)),
        pa.field("effect_details", pa.list_(effect_details)),
        pa.field("af_parents_called_count", pa.int32()),
        pa.field("af_parents_called_percent", pa.float32()),
        pa.field("af_alternative_allele_count", pa.int32()),
        pa.field("af_alternative_allele_freq", pa.float32()),
        pa.field("af_reference_allele_count", pa.int32()),
        pa.field("af_reference_allele_freq", pa.float32())
    ]

    return pa.schema(fields)


def summary_parquet_schema_flat():

    fields = [
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int64()),
        pa.field("reference", pa.string()),
        pa.field("alternative", pa.string()),
        pa.field("var_index", pa.int64()),
        pa.field("allele_index", pa.int8()),
        pa.field("split_from_multi_allelic", pa.bool_()),
        pa.field("effect_type", pa.string()),
        pa.field("effect_gene.genes", pa.list_(pa.string())),
        pa.field("effect_gene.types", pa.list_(pa.string())),
        pa.field("effect_details.transcript_ids", pa.list_(pa.string())),
        pa.field("effect_details.details", pa.list_(pa.string())),
        pa.field("af_parents_called_count", pa.int32()),
        pa.field("af_parents_called_percent", pa.float64()),
        pa.field("af_alternative_allele_count", pa.int32()),
        pa.field("af_alternative_allele_freq", pa.float64()),
        pa.field("af_reference_allele_count", pa.int32()),
        pa.field("af_reference_allele_freq", pa.float64()),
        # pa.field("ultra_rare", pa.bool_()),
    ]

    return pa.schema(fields)


def summary_batch(sum_df):
    schema = summary_parquet_schema_flat()

    batch_data = []
    for name in schema.names:
        assert name in sum_df
        data = sum_df[name].values
        field = schema.field_by_name(name)
        # print("storing field: ", name)
        batch_data.append(pa.array(data, type=field.type))

    batch = pa.RecordBatch.from_arrays(
        batch_data,
        schema.names)

    return batch


def summary_table(sum_df):
    batch = summary_batch(sum_df)
    table = pa.Table.from_batches([batch])
    return table


def save_summary_to_parquet(sum_df, filename):
    table = summary_table(sum_df)
    pq.write_table(table, filename)


def read_summary_from_parquet(filename):
    schema = summary_parquet_schema_flat()
    table = pq.read_table(filename, columns=schema.names)
    df = table.to_pandas()
    return df


def family_variant_parquet_schema():
    fields = [
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int64()),
        pa.field("reference", pa.string()),
        pa.field("alternative", pa.string()),
        pa.field("var_index", pa.int64()),
        pa.field("allele_index", pa.int8()),
        pa.field("split_from_multi_allelic", pa.bool_()),
        pa.field("family_id", pa.string()),
        pa.field("genotype", pa.list_(pa.int8())),
        pa.field("inheritance", pa.int32()),
        pa.field("variant_in_members", pa.list_(pa.string())),
        pa.field("variant_in_roles", pa.list_(pa.int32())),
        pa.field("variant_in_sexes", pa.list_(pa.int8())),
    ]

    return pa.schema(fields)


def family_variants_batch(variants):
    schema = family_variant_parquet_schema()
    data = {
        "chrom": [],
        "position": [],
        "reference": [],
        "alternative": [],
        "var_index": [],
        "allele_index": [],
        "split_from_multi_allelic": [],
        "family_id": [],
        "genotype": [],
        "inheritance": [],
        "variant_in_members": [],
        "variant_in_roles": [],
        "variant_in_sexes": [],
    }
    for vs in variants:
        # assert vs.inheritance != Inheritance.reference
        for v in vs:
            data["chrom"].append(v.chromosome)
            data["position"].append(v.position)
            data["reference"].append(v.reference)
            data["alternative"].append(v.alternative)
            data["var_index"].append(v.var_index)
            data["allele_index"].append(v.allele_index)
            data["split_from_multi_allelic"].append(v.split_from_multi_allelic)
            data["family_id"].append(v.family_id)
            data["genotype"].append(v.gt_flatten())
            data["inheritance"].append(v.inheritance.value)
            data["variant_in_members"].append(
                [unicode(m, "utf-8") for m in v.variant_in_members])
            data["variant_in_roles"].append(
                [r.value for r in v.variant_in_roles])
            data["variant_in_sexes"].append(
                [s.value for s in v.variant_in_sexes])

    batch_data = []
    for name in schema.names:
        assert name in data
        column = data[name]
        field = schema.field_by_name(name)
        batch_data.append(pa.array(column, type=field.type))

    batch = pa.RecordBatch.from_arrays(
        batch_data,
        schema.names)
    return batch


def family_variants_df_batch(vars_df):
    schema = family_variant_parquet_schema()

    batch_data = []
    for name in schema.names:
        assert name in vars_df
        data = vars_df[name].values
        field = schema.field_by_name(name)
        batch_data.append(pa.array(data, type=field.type))

    batch = pa.RecordBatch.from_arrays(
        batch_data,
        schema.names)

    return batch


def family_variants_table(variants):
    batch = family_variants_batch(variants)
    table = pa.Table.from_batches([batch])
    return table


def family_variants_df(variants):
    table = family_variants_table(variants)
    return table.to_pandas()


def family_variants_df_table(vars_df):
    batch = family_variants_df_batch(vars_df)
    table = pa.Table.from_batches([batch])
    return table


def save_family_variants_df_to_parquet(vars_df, filename):
    table = family_variants_df_table(vars_df)
    pq.write_table(table, filename)


def read_family_variants_df_from_parquet(filename):
    schema = family_variant_parquet_schema()
    table = pq.read_table(filename, columns=schema.names)
    df = table.to_pandas()
    return df
