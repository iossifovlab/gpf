import sys
import time
import itertools
import traceback
import tempfile

from collections import namedtuple

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from annotation.tools.file_io_parquet import ParquetSchema
from backends.impala.serializers import FamilyVariantSerializer


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
        for name in self.schema.names:
            assert name in self.data
            column = self.data[name]
            field = self.schema.field_by_name(name)
            batch_data.append(pa.array(column, type=field.type))
        batch = pa.RecordBatch.from_arrays(batch_data, self.schema.names)
        return batch

    def build_table(self):
        batch = self.build_batch()
        self.data_reset()
        return pa.Table.from_batches([batch])

    def __len__(self):
        return len(self.data['summary_variant_index'])


class ParquetSerializer(object):

    summary = namedtuple(
        'summary', [
            'summary_variant_index',
            'allele_index',
            'chrom',
            'position',
            'reference',
            'alternative',
            'variant_type',
            'worst_effect',
            'af_parents_called_count',
            'af_parents_called_percent',
            'af_allele_count',
            'af_allele_freq'
        ])

    effect_gene = namedtuple(
        'effect_gene', [
            'effect_type',
            'effect_gene'
        ]
    )

    family = namedtuple(
        'family', [
            'family_variant_index',
            'family_id',
            'is_denovo',
        ]
    )

    member = namedtuple(
        'member', [
            'variant_in_member',
            'variant_in_role',
            'variant_in_sex',
            'inheritance_in_member',
        ]
    )

    def __init__(self, include_reference=True, annotation_schema=None):
        self.include_reference = include_reference
        self.annotation_schema = annotation_schema

    def serialize_summary(self, summary_variant_index, allele):
        if not self.include_reference and allele.is_reference_allele:
            return None
        elif allele.is_reference_allele:
            return self.summary(
                summary_variant_index,
                allele.allele_index,
                allele.chrom,
                allele.position,
                allele.reference,
                None,
                None,
                None,
                allele.get_attribute('af_parents_called_count'),
                allele.get_attribute('af_parents_called_percent'),
                allele.get_attribute('af_allele_count'),
                allele.get_attribute('af_allele_freq')
            )
        else:
            return self.summary(
                summary_variant_index,
                allele.allele_index,
                allele.chrom,
                allele.position,
                allele.reference,
                allele.alternative,
                allele.variant_type.value,
                allele.effect.worst,
                allele.get_attribute('af_parents_called_count'),
                allele.get_attribute('af_parents_called_percent'),
                allele.get_attribute('af_allele_count'),
                allele.get_attribute('af_allele_freq')
            )

    def serialize_effects(self, allele):
        if allele.is_reference_allele:
            return self.effect_gene(None, None)
        return [
            self.effect_gene(eg.effect, eg.symbol)
            for eg in allele.effect.genes
        ]

    def serialize_family(self, family_variant_index, family):
        return self.family(
            family_variant_index,
            family.family_id,
            family.get_attribute('is_denovo')
        )

    def serialize_members(self, family_variant_index, family):
        result = []
        for variant_in_member, variant_in_role, \
                variant_in_sex, inheritance_in_member in zip(
                    family.variant_in_members,
                    family.variant_in_roles,
                    family.variant_in_sexes,
                    family.inheritance_in_members):

            if variant_in_member is None:
                continue
            result.append(self.member(
                variant_in_member,
                variant_in_role.value,
                variant_in_sex.value,
                inheritance_in_member.value))

        return result


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
        pa.field("af_parents_called_count", pa.int32()),
        pa.field("af_parents_called_percent", pa.float32()),
        pa.field("af_allele_count", pa.int32()),
        pa.field("af_allele_freq", pa.float32()),

        pa.field("effect_type", pa.string()),
        pa.field("effect_gene", pa.string()),

        pa.field("family_variant_index", pa.int64()),
        pa.field("family_id", pa.string()),
        pa.field("is_denovo", pa.bool_()),

        pa.field("variant_in_member", pa.string()),
        pa.field("variant_in_role", pa.int8()),
        pa.field("variant_in_sex", pa.int8()),
        pa.field("inheritance_in_member", pa.int8()),

        pa.field("data", pa.binary()),
    ])

    def __init__(self, full_variants_iterator, annotation_schema=None):
        self.full_variants_iterator = full_variants_iterator

        if annotation_schema is not None:
            base_schema = ParquetSchema.from_arrow(self.SCHEMA)
            schema = ParquetSchema.merge_schemas(
                base_schema, annotation_schema).to_arrow()
        else:
            schema = self.SCHEMA

        self.start = time.time()
        self.data = ParquetData(schema)

    def variants_table(self, bucket_index=0, batch_size=100000):
        variant_serializer = FamilyVariantSerializer(None)
        parquet_serializer = ParquetSerializer()

        family_variant_index = 0

        for summary_variant_index, (_, family_variants) in \
                enumerate(self.full_variants_iterator):

            for family_variant in family_variants:
                family_variant_index += 1

                data = variant_serializer.serialize(family_variant)
                for family_allele in family_variant.alleles:
                    summary = parquet_serializer.serialize_summary(
                        summary_variant_index, family_allele
                    )
                    effect_genes = parquet_serializer.serialize_effects(
                        family_allele)
                    family = parquet_serializer.serialize_family(
                        family_variant_index, family_allele)
                    member = parquet_serializer.serialize_members(
                        family_variant_index, family_allele)

                    for (d, s, e, f, m) in itertools.product(
                            [data], [summary], effect_genes, [family], member):

                        self.data.data_append('data', d)
                        self.data.data_append('bucket_index', bucket_index)

                        for d in (s, e, f, m):
                            for key, val in d._asdict().items():
                                self.data.data_append(key, val)

            if family_variant_index % 1000 == 0:
                elapsed = time.time() - self.start
                print("{} family variants imported for {:.2f} sec".format(
                       family_variant_index, elapsed),
                      file=sys.stderr)

            if len(self.data) >= batch_size:
                table = self.data.build_table()

                yield table

        if len(self.data) > 0:
            table = self.data.build_table()

            yield table

        elapsed = time.time() - self.start
        print("DONE: {} family variants imported for {:.2f} sec".format(
                family_variant_index, elapsed),
              file=sys.stderr)

    def save_variants_to_parquet(
            self, filename=None, bucket_index=1, batch_size=100000,
            filesystem=None):

        writer = pq.ParquetWriter(
            filename, self.data.schema, filesystem=filesystem)

        try:
            for table in self.variants_table(bucket_index, batch_size):
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


class HdfsHelpers(object):

    def __init__(self, host=None, port=0):
        self.host = host
        self.port = port
        self.hdfs = pa.hdfs.connect(host=self.host, port=self.port)

    def exists(self, path):
        return self.hdfs.exists(path)

    def mkdir(self, path):
        print(path)
        self.hdfs.mkdir(path)
        self.chmod(path, 0o777)

    def tempdir(self, prefix='', suffix=''):
        dirname = tempfile.mktemp(prefix=prefix, suffix=suffix)
        self.mkdir(dirname)
        assert self.exists(dirname)

        return dirname

    def chmod(self, path, mode):
        return self.hdfs.chmod(path, mode)

    def delete(self, path, recursive=False):
        return self.hdfs.delete(path, recursive=recursive)

    def filesystem(self):
        return self.hdfs
