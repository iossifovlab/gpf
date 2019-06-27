import sys
import time
import itertools
import traceback
from collections import defaultdict

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from backends.impala.serializers import ParquetSerializer


class ParquetData(object):

    def __init__(self, schema):
        self.schema = schema
        self.data_reset()

    def data_reset(self):
        self.data = {
            name: [] for name in self.schema.names
        }

    def data_append(self, attr_name, value):
        self.data[attr_name].append(value)

    def data_append_enum_array(self, attr_name, value, dtype=np.int8):
        self.data[attr_name].append(
            np.asarray(
                [v.value for v in value if v is not None],
                dtype=dtype))

    def data_append_str_array(self, attr_name, value):
        self.data[attr_name].append(
            [str(v) for v in value if v is not None])

    def build_batch(self):
        batch_data = []
        for index, name in enumerate(self.schema.names):
            assert name in self.data
            column = self.data[name]
            field = self.schema.field_by_name(name)
            batch_data.append(pa.array(column, type=field.type))
            if index > 0:
                assert len(batch_data[index]) == len(batch_data[0]), name
        batch = pa.RecordBatch.from_arrays(batch_data, self.schema.names)
        return batch

    def build_table(self):
        batch = self.build_batch()
        self.data_reset()
        return pa.Table.from_batches([batch])

    def __len__(self):
        return len(self.data['summary_variant_index'])


class VariantsParquetWriter(object):

    SCHEMA = pa.schema([
        pa.field("bucket_index", pa.int32()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int8()),
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int32()),
        pa.field("reference", pa.string()),
        pa.field("alternative", pa.string()),
        pa.field("variant_type", pa.int8()),
        pa.field("worst_effect", pa.string()),
        pa.field("alternatives_data", pa.string()),

        pa.field("effect_type", pa.string()),
        pa.field("effect_gene", pa.string()),
        pa.field("effect_data", pa.string()),

        pa.field("family_variant_index", pa.int64()),
        pa.field("family_id", pa.string()),
        pa.field("is_denovo", pa.bool_()),

        pa.field("variant_sexes", pa.int8()),
        pa.field("variant_roles", pa.int32()),
        pa.field("variant_inheritance", pa.int16()),

        pa.field("variant_in_member", pa.string()),
        pa.field("genotype_data", pa.string()),

        pa.field('af_parents_called_count', pa.int32()),
        pa.field('af_parents_called_percent', pa.float32()),
        pa.field('af_allele_count', pa.int32()),
        pa.field('af_allele_freq', pa.float32()),
        pa.field('frequency_data', pa.string()),

    ])

    EXCLUDE = [
        'effect_gene_genes',
        'effect_gene_types',
        'effect_genes',
        'effect_details_transcript_ids',
        'effect_details_details',
        'effect_details',
    ]

    def __init__(self, full_variants_iterator, annotation_schema=None):
        self.full_variants_iterator = full_variants_iterator

        if annotation_schema is not None:
            # base_schema = ParquetSchema.from_arrow(self.SCHEMA)
            # print("base_schema:", base_schema)
            # print("annotation_schema:", annotation_schema)
            print("!!!ANNOTATION SCHEMA NOT APPLIED!!!")
            # schema = ParquetSchema.merge_schemas(
            #     base_schema, annotation_schema).to_arrow()
            schema = self.SCHEMA
        else:
            schema = self.SCHEMA

        self.start = time.time()
        self.data = ParquetData(schema)

    def variants_table(self, bucket_index=0, rows=10000):
        parquet_serializer = ParquetSerializer()
        print("row group size:", rows)

        family_variant_index = 0
        histogram = defaultdict(lambda: 0)
        for summary_variant_index, (_, family_variants) in \
                enumerate(self.full_variants_iterator):

            for family_variant in family_variants:
                family_variant_index += 1
                effect_data = parquet_serializer.serialize_variant_effects(
                    family_variant.effects
                )
                alternatives_data = family_variant.alternative
                genotype_data = parquet_serializer.serialize_variant_genotype(
                    family_variant.gt
                )
                frequency_data = \
                    parquet_serializer.serialize_variant_frequency(
                        family_variant
                    )

                repetition = 0
                for family_allele in family_variant.alleles:
                    summary = parquet_serializer.serialize_summary(
                        summary_variant_index, family_allele,
                        alternatives_data
                    )
                    frequency = parquet_serializer.serialize_alelle_frequency(
                        family_allele, frequency_data
                    )
                    effect_genes = parquet_serializer.serialize_effects(
                        family_allele, effect_data)
                    family = parquet_serializer.serialize_family(
                        family_variant_index, family_allele, genotype_data)
                    member = parquet_serializer.serialize_members(
                        family_variant_index, family_allele)

                    for (s, freq, e, f, m) in itertools.product(
                            [summary], [frequency], effect_genes,
                            [family], member):

                        repetition += 1

                        self.data.data_append('bucket_index', bucket_index)

                        for d in (s, freq, e, f, m):
                            for key, val in d._asdict().items():
                                self.data.data_append(key, val)
                histogram[repetition] += 1

            if family_variant_index % 1000 == 0:
                elapsed = time.time() - self.start
                print(
                    "Bucket {}: {} family variants imported for {:.2f} sec".
                    format(
                        bucket_index,
                        family_variant_index, elapsed),
                    file=sys.stderr)

            if len(self.data) >= rows:
                table = self.data.build_table()

                yield table

        if len(self.data) > 0:
            table = self.data.build_table()

            yield table

        print("-------------------------------------------", file=sys.stderr)
        print("Bucket:", bucket_index, file=sys.stderr)
        print("-------------------------------------------", file=sys.stderr)
        elapsed = time.time() - self.start
        print(
            "DONE: {} family variants imported for {:.2f} sec".
            format(
                family_variant_index, elapsed),
            file=sys.stderr)
        print("-------------------------------------------", file=sys.stderr)
        for r, c in histogram.items():
            print(r, c, file=sys.stderr)
        print("-------------------------------------------", file=sys.stderr)

    def save_variants_to_parquet(
            self, filename=None, bucket_index=1, rows=100000,
            filesystem=None):

        compression = {
            b"bucket_index": "SNAPPY",
            b"summary_variant_index": "SNAPPY",
            b"allele_index": "SNAPPY",
            b"chrom": "SNAPPY",
            b"position": "SNAPPY",
            b"reference": "SNAPPY",
            b"alternative": "SNAPPY",
            b"variant_type": "SNAPPY",
            b"worst_effect": "SNAPPY",
            b"af_parents_called_count": "SNAPPY",
            b"af_parents_called_percent": "SNAPPY",
            b"af_allele_count": "SNAPPY",
            b"af_allele_freq": "SNAPPY",

            b"effect_type": "SNAPPY",
            b"effect_gene": "SNAPPY",

            b"family_variant_index": "SNAPPY",
            b"family_id": "SNAPPY",
            b"is_denovo": "SNAPPY",

            b"variant_sexes": "SNAPPY",
            b"variant_roles": "SNAPPY",
            b"variant_sexes": "SNAPPY",
            b"variant_inheritance": "SNAPPY",
            b"variant_in_member": "SNAPPY",

            b"alternatives_data": "SNAPPY",
            b"effect_data": "SNAPPY",
            b"genotype_data": "SNAPPY",
        }

        writer = pq.ParquetWriter(
            filename, self.data.schema,
            compression=compression, filesystem=filesystem)

        try:
            for table in self.variants_table(
                    bucket_index=bucket_index, rows=rows):
                assert table.schema == self.data.schema
                writer.write_table(table)

        except Exception as ex:
            print("unexpected error:", ex)
            traceback.print_exc(file=sys.stdout)
        finally:
            writer.close()


def pedigree_parquet_schema():
    fields = [
        pa.field("family_id", pa.string()),
        pa.field("person_id", pa.string()),
        pa.field("dad_id", pa.string()),
        pa.field("mom_id", pa.string()),
        pa.field("sex", pa.int8()),
        pa.field("status", pa.int8()),
        pa.field("role", pa.int32()),
        pa.field("sample_id", pa.string()),
    ]

    return pa.schema(fields)


def save_ped_df_to_parquet(ped_df, filename, filesystem=None):

    ped_df = ped_df.copy()
    ped_df.role = ped_df.role.apply(lambda r: r.value)
    ped_df.sex = ped_df.sex.apply(lambda s: s.value)
    ped_df.status = ped_df.status.apply(lambda s: s.value)

    table = pa.Table.from_pandas(ped_df, schema=pedigree_parquet_schema())
    pq.write_table(table, filename, filesystem=filesystem)
