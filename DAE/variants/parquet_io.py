'''
Created on May 30, 2018

@author: lubo
'''
from __future__ import print_function

import sys
import traceback

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from tqdm import tqdm

from variants.attributes import Role, Sex


def summary_parquet_schema_flat():

    fields = [
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int64()),
        pa.field("reference", pa.string()),
        pa.field("alternative", pa.string()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int16()),
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
        # pa.field("ultra_rare", pa.bool_()),
    ]

    return pa.schema(fields)


def summary_variants_batch(variants):
    schema = summary_parquet_schema_flat()
    data = {
        name: [] for name in schema.names
    }
    with tqdm() as pbar:

        for v in variants:
            for a in v.alleles:
                pbar.update()
                for name in schema.names:
                    data[name].append(a.get_attribute(name))

    return batch_from_data_dict(data, schema)


def summary_variants_table(variants):
    batch = summary_variants_batch(variants)
    table = pa.Table.from_batches([batch])
    return table


def save_summary_variants_to_parquet(variants, summary_filename):
    summary_table = summary_variants_table(variants)
    pq.write_table(summary_table, summary_filename)


def batch_from_data_dict(data, schema):
    batch_data = []
    for name in schema.names:
        assert name in data
        column = data[name]
        field = schema.field_by_name(name)
        if field.type == pa.string() and not isinstance(column[0], unicode):
            column = [
                unicode(v, 'utf-8') if v is not None else None
                for v in column
            ]
        batch_data.append(pa.array(column, type=field.type))
    batch = pa.RecordBatch.from_arrays(batch_data, schema.names)
    return batch


def table_from_data_dict(data, schema):
    batch = batch_from_data_dict(data, schema)
    return pa.Table.from_batches([batch])


def summary_batch(sum_df):
    schema = summary_parquet_schema_flat()

    batch_data = []
    for name in schema.names:
        assert name in sum_df, name
        print("summary batch: field=", name)
        data = sum_df[name].values
        field = schema.field_by_name(name)
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
        pa.field("family_id", pa.string()),
        pa.field("family_index", pa.int32()),
        pa.field("family_variant_index", pa.int64()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("genotype", pa.list_(pa.int64())),
    ]

    return pa.schema(fields)


def family_allele_parquet_schema():
    fields = [
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int64()),
        pa.field("family_id", pa.string()),
        pa.field("family_index", pa.int32()),
        pa.field("family_variant_index", pa.int64()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int8()),
        pa.field("inheritance_in_members", pa.list_(pa.int64())),
        pa.field("variant_in_members", pa.list_(pa.string())),
        pa.field("variant_in_roles", pa.list_(pa.int64())),
        pa.field("variant_in_sexes", pa.list_(pa.int64())),
    ]
    return pa.schema(fields)


def setup_family_batch_data():
    return {
        "chrom": [],
        "position": [],
        "family_id": [],
        "family_index": [],
        "family_variant_index": [],
        "summary_variant_index": [],
        "genotype": [],
    }


def setup_allele_batch_data():
    return {
        "chrom": [],
        "position": [],
        "family_id": [],
        "family_index": [],
        "family_variant_index": [],
        "summary_variant_index": [],
        "allele_index": [],
        "inheritance_in_members": [],
        "variant_in_members": [],
        "variant_in_roles": [],
        "variant_in_sexes": [],
    }


def family_variants_table(variants, batch_size=1000000):
    family_schema = family_variant_parquet_schema()
    family_allele_schema = family_allele_parquet_schema()

    allele_data = setup_allele_batch_data()
    family_data = setup_family_batch_data()

    with tqdm() as pbar:

        for family_variant_index, vs in enumerate(variants):
            pbar.update()

            for allele in vs.alleles:
                allele_data["chrom"].append(vs.chromosome)
                allele_data["position"].append(vs.position)
                allele_data["family_id"].append(vs.family_id)
                allele_data["family_index"].append(vs.family_index)
                allele_data["family_variant_index"].append(
                    family_variant_index)
                allele_data["summary_variant_index"].append(vs.summary_index)
                allele_data["allele_index"].append(allele.allele_index)
                allele_data["inheritance_in_members"].\
                    append(
                        np.asarray([
                            i.value for i in allele.inheritance_in_members
                        ], dtype=np.int64))
                if allele.is_reference_allele:
                    allele_data["variant_in_members"].append(None)
                    allele_data["variant_in_roles"].append(None)
                    allele_data["variant_in_sexes"].append(None)
                else:
                    allele_data["variant_in_members"].append(
                        [unicode(m, "utf-8")
                         for m in allele.variant_in_members])
                    allele_data["variant_in_roles"].append(
                        [r.value for r in allele.variant_in_roles])
                    allele_data["variant_in_sexes"].append(
                        [s.value for s in allele.variant_in_sexes])

            family_data["chrom"].append(vs.chromosome)
            family_data["position"].append(vs.position)
            family_data["family_id"].append(vs.family_id)
            family_data["family_index"].append(vs.family_index)
            family_data["family_variant_index"].append(family_variant_index)
            family_data["summary_variant_index"].append(vs.summary_index)
            family_data["genotype"].append(vs.gt_flatten())

            if (family_variant_index + 1) % batch_size == 0:

                allele_table = table_from_data_dict(
                    allele_data, family_allele_schema)

                family_table = table_from_data_dict(
                    family_data, family_schema)

                allele_data = setup_allele_batch_data()
                family_data = setup_family_batch_data()

                yield family_table, allele_table

        if len(allele_data) > 0 and len(family_data) > 0:
            allele_table = table_from_data_dict(
                allele_data, family_allele_schema)
            family_table = table_from_data_dict(family_data, family_schema)

            yield family_table, allele_table


def save_family_variants_to_parquet(
        variants, family_filename, allele_filename, batch_size=100000):
    family_schema = family_variant_parquet_schema()
    allele_schema = family_allele_parquet_schema()

    family_writer = pq.ParquetWriter(family_filename, family_schema)
    allele_writer = pq.ParquetWriter(allele_filename, allele_schema)
    try:
        for ftable, atable in family_variants_table(variants, batch_size):
            assert ftable.schema == family_schema
            assert atable.schema == allele_schema
            assert ftable.num_rows > 0
            assert atable.num_rows > 0
            family_writer.write_table(ftable)
            allele_writer.write_table(atable)

    except Exception as ex:
        print("unexpected error:", ex)
        traceback.print_exc(file=sys.stdout)
    finally:
        family_writer.close()
        allele_writer.close()


def family_variants_df_to_batch(vars_df):
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


def family_allele_df_to_batch(f2s_df):
    schema = family_allele_parquet_schema()

    batch_data = []
    for name in schema.names:
        assert name in f2s_df
        data = f2s_df[name].values
        field = schema.field_by_name(name)
        batch_data.append(pa.array(data, type=field.type))

    batch = pa.RecordBatch.from_arrays(
        batch_data,
        schema.names)

    return batch


def family_variants_df(variants):
    for ftable, atable in family_variants_table(variants):
        return ftable.to_pandas(), atable.to_pandas()


def save_family_variants_df_to_parquet(vars_df, filename):
    batch = family_variants_df_to_batch(vars_df)
    table = pa.Table.from_batches([batch])
    pq.write_table(table, filename)


def read_family_variants_df_from_parquet(filename):
    schema = family_variant_parquet_schema()
    table = pq.read_table(filename, columns=schema.names)
    df = table.to_pandas()
    return df


def save_family_allele_df_to_parquet(f2s_df, filename):
    batch = family_allele_df_to_batch(f2s_df)
    table = pa.Table.from_batches([batch])
    pq.write_table(table, filename)


def read_family_allele_df_from_parquet(filename):
    schema = family_allele_parquet_schema()
    table = pq.read_table(filename, columns=schema.names)
    df = table.to_pandas()
    return df


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

    table = pa.Table.from_pandas(ped_df)
    pq.write_table(table, filename)


def read_ped_df_from_parquet(filename):
    table = pq.read_table(filename)
    ped_df = table.to_pandas()
    ped_df.role = ped_df.role.apply(lambda v: Role(v))
    ped_df.sex = ped_df.sex.apply(lambda v: Sex(v))

    return ped_df
