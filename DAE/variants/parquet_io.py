'''
Created on May 30, 2018

@author: lubo
'''
from __future__ import print_function
import pyarrow as pa
import pyarrow.parquet as pq


def annotation_parquet_schema():
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


def annotation_parquet_schema_flat():
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
        pa.field("effect_gene.genes", pa.list_(pa.binary())),
        pa.field("effect_gene.types", pa.list_(pa.binary())),
        pa.field("effect_details.transcript_ids", pa.list_(pa.binary())),
        pa.field("effect_details.details", pa.list_(pa.binary())),
        pa.field("af_parents_called_count", pa.int32()),
        pa.field("af_parents_called_percent", pa.float64()),
        pa.field("af_alternative_allele_count", pa.int32()),
        pa.field("af_alternative_allele_freq", pa.float64()),
        pa.field("af_reference_allele_count", pa.int32()),
        pa.field("af_reference_allele_freq", pa.float64())
    ]

    return pa.schema(fields)


def annotation_table(annot_df):
    schema = annotation_parquet_schema_flat()
    print(dir(schema))

    batch_data = []
    for name in schema.names:
        assert name in annot_df
        data = annot_df[name].values
        print(name, type(data), data)
        field = schema.field_by_name(name)
        print(field.type)
        batch_data.append(pa.array(data, type=field.type))

    batch = pa.RecordBatch.from_arrays(
        batch_data,
        schema.names)

    table = pa.Table.from_batches([batch])
    return table


def save_annotation_to_parquet(annot_df, filename):
    table = annotation_table(annot_df)
    pq.write_table(table, filename)


def read_annotation_from_parquet(filename):
    schema = annotation_parquet_schema_flat()
    table = pq.read_table(filename, columns=schema.names)
    df = table.to_pandas()
    return df
