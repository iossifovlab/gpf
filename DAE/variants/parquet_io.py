'''
Created on May 30, 2018

@author: lubo
'''
from __future__ import print_function
import pyarrow as pa
import pyarrow.parquet as pq
from variants.attributes import Role, Sex


def summary_parquet_schema_flat():

    fields = [
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int64()),
        pa.field("reference", pa.string()),
        pa.field("alternative", pa.string()),
        pa.field("summary_index", pa.int64()),
        pa.field("allele_index", pa.int16()),
        pa.field("variant_type", pa.int8()),
        pa.field("cshl_variant", pa.string()),
        pa.field("cshl_position", pa.int64()),
        pa.field("cshl_length", pa.int32()),
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


def summary_batch(sum_df):
    schema = summary_parquet_schema_flat()

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
        pa.field("family_index", pa.int64()),
        pa.field("summary_index", pa.int64()),
        pa.field("family_id", pa.string()),
        pa.field("genotype", pa.list_(pa.int8())),
        # pa.field("inheritance", pa.int32()),
    ]

    return pa.schema(fields)


def f2s_parquet_schema():
    fields = [
        pa.field("family_index", pa.int64()),
        pa.field("summary_index", pa.int64()),
        pa.field("allele_index", pa.int16()),
        pa.field("variant_in_members", pa.list_(pa.string())),
        pa.field("variant_in_roles", pa.list_(pa.int32())),
        pa.field("variant_in_sexes", pa.list_(pa.int8())),
    ]
    return pa.schema(fields)


def family_variants_batch(variants):
    family_schema = family_variant_parquet_schema()
    f2s_schema = f2s_parquet_schema()

    family_data = {
        "chrom": [],
        "position": [],
        "family_index": [],
        "summary_index": [],
        "family_id": [],
        "genotype": [],
        "inheritance": [],
    }
    f2s_data = {
        "family_index": [],
        "summary_index": [],
        "allele_index": [],
        "variant_in_members": [],
        "variant_in_roles": [],
        "variant_in_sexes": [],
    }
    for family_index, vs in enumerate(variants):
        for allele in vs.alleles:
            f2s_data["family_index"].append(family_index)
            f2s_data["summary_index"].append(vs.summary_index)
            f2s_data["allele_index"].append(allele.allele_index)
            if allele.is_reference_allele:
                f2s_data["variant_in_members"].append(None)
                f2s_data["variant_in_roles"].append(None)
                f2s_data["variant_in_sexes"].append(None)
            else:
                f2s_data["variant_in_members"].append(
                    [unicode(m, "utf-8") for m in allele.variant_in_members])
                f2s_data["variant_in_roles"].append(
                    [r.value for r in allele.variant_in_roles])
                f2s_data["variant_in_sexes"].append(
                    [s.value for s in allele.variant_in_sexes])

        family_data["chrom"].append(vs.chromosome)
        family_data["position"].append(vs.position)
        family_data["family_index"].append(family_index)
        family_data["summary_index"].append(vs.summary_index)
        family_data["family_id"].append(vs.family_id)
        family_data["genotype"].append(vs.gt_flatten())
        family_data["inheritance"].append(None)

    f2s_batch_data = []
    for name in f2s_schema.names:
        assert name in f2s_data
        column = f2s_data[name]
        field = f2s_schema.field_by_name(name)
        f2s_batch_data.append(pa.array(column, type=field.type))
    f2s_batch = pa.RecordBatch.from_arrays(
        f2s_batch_data,
        f2s_schema.names)

    family_batch_data = []
    for name in family_schema.names:
        assert name in family_data
        column = family_data[name]
        field = family_schema.field_by_name(name)
        family_batch_data.append(pa.array(column, type=field.type))

    family_batch = pa.RecordBatch.from_arrays(
        family_batch_data,
        family_schema.names)
    return family_batch, f2s_batch


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


def f2s_df_to_batch(f2s_df):
    schema = f2s_parquet_schema()

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


def family_variants_table(variants):
    family_batch, f2s_batch = family_variants_batch(variants)
    family_table = pa.Table.from_batches([family_batch])
    f2s_table = pa.Table.from_batches([f2s_batch])
    return family_table, f2s_table


def family_variants_df(variants):
    family_table, f2s_table = family_variants_table(variants)
    return family_table.to_pandas(), f2s_table.to_pandas()


def save_family_variants_df_to_parquet(vars_df, filename):
    batch = family_variants_df_to_batch(vars_df)
    table = pa.Table.from_batches([batch])
    pq.write_table(table, filename)


def read_family_variants_df_from_parquet(filename):
    schema = family_variant_parquet_schema()
    table = pq.read_table(filename, columns=schema.names)
    df = table.to_pandas()
    return df


def save_f2s_df_to_parquet(f2s_df, filename):
    batch = f2s_df_to_batch(f2s_df)
    table = pa.Table.from_batches([batch])
    pq.write_table(table, filename)


def read_f2s_df_from_parquet(filename):
    schema = f2s_parquet_schema()
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
