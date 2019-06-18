import os
import sys
import time
import itertools
import traceback
import tempfile
import operator
import functools

from variants.effects import Effect

from collections import namedtuple, defaultdict

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from variants.variant import SummaryAllele, SummaryVariant
from variants.family_variant import FamilyVariant
from utils.vcf_utils import GENOTYPE_TYPE


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
            'af_allele_freq',
            'alternatives_data',
        ])

    effect_gene = namedtuple(
        'effect_gene', [
            'effect_type',
            'effect_gene',
            'effect_data',
        ]
    )

    family = namedtuple(
        'family', [
            'family_variant_index',
            'family_id',
            'is_denovo',
            'variant_sexes',
            'variant_roles',
            'variant_inheritance',
            'genotype_data',
        ]
    )

    member = namedtuple(
        'member', [
            'variant_in_member',
            # 'variant_in_role',
            # 'variant_in_sex',
            # 'inheritance_in_member',
        ]
    )

    def __init__(
            self, include_reference=True, annotation_schema=None):
        # self.families = families
        self.include_reference = include_reference
        self.annotation_schema = annotation_schema

    def serialize_summary(
            self, summary_variant_index, allele, alternatives_data):
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
                allele.get_attribute('af_allele_freq'),
                alternatives_data,
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
                allele.get_attribute('af_allele_freq'),
                alternatives_data,
            )

    def serialize_effects(self, allele, effect_data):
        if allele.is_reference_allele:
            return self.effect_gene(None, None, effect_data)
        return [
            self.effect_gene(eg.effect, eg.symbol, effect_data)
            for eg in allele.effect.genes
        ]

    @staticmethod
    def serialize_variant_genotype(gt):
        rows, _ = gt.shape
        assert rows == 2
        flat = gt.flatten(order='F')
        buff = flat.tobytes()
        data = str(buff, 'latin1')

        return data

    @staticmethod
    def deserialize_variant_genotype(data):
        buff = bytes(data, 'latin1')
        gt = np.frombuffer(buff, dtype=GENOTYPE_TYPE)
        assert len(gt) % 2 == 0

        size = len(gt) // 2
        gt = gt.reshape([2, size], order='F')
        return gt

    @staticmethod
    def serialize_variant_alternatives(alternatives):
        return ",".join(alternatives)

    @staticmethod
    def deserialize_variant_alternatives(data):
        return data.split(",")

    @staticmethod
    def serialize_variant_effects(effects):
        if effects is None:
            return None
        return "#".join([str(e) for e in effects])

    @staticmethod
    def deserialize_variant_effects(data):
        return [Effect.from_string(e) for e in data.split("#")]

    def serialize_family(
            self, family_variant_index, family_allele, genotype_data):
        res = self.family(
            family_variant_index,
            family_allele.family_id,
            family_allele.get_attribute('is_denovo'),
            functools.reduce(
                operator.or_, [
                    vs.value for vs in family_allele.variant_in_sexes
                    if vs is not None
                ], 0),
            functools.reduce(
                operator.or_, [
                    vr.value for vr in family_allele.variant_in_roles
                    if vr is not None
                ], 0),
            functools.reduce(
                operator.or_, [
                    vi.value for vi in family_allele.inheritance_in_members
                    if vi is not None
                ], 0),
            genotype_data,
        )
        return res

    def serialize_members(self, family_variant_index, family):
        result = []
        for variant_in_member in family.variant_in_members:
            if variant_in_member is None:
                continue
            result.append(self.member(variant_in_member))
        return result

    def deserialize_variant(
            self, family,
            chrom, position, reference, alternatives_data, 
            effect_data, genotype_data):
        effects = ParquetSerializer.deserialize_variant_effects(
            effect_data)
        alternatives = ParquetSerializer.deserialize_variant_alternatives(
            alternatives_data
        )
        assert len(effects) == len(alternatives)

        # family = self.families.get(family_id)
        assert family is not None

        genotype = ParquetSerializer.deserialize_variant_genotype(
            genotype_data)
        rows, cols = genotype.shape
        assert cols == len(family)

        alleles = []
        for alt, effect in zip(alternatives, effects):
            allele = SummaryAllele(
                chrom, position, reference, alt, effect=effect)
            alleles.append(allele)
        return FamilyVariant(
            SummaryVariant(alleles),
            family,
            genotype
        )


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

        # pa.field("data", pa.binary()),
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

                repetition = 0
                for family_allele in family_variant.alleles:
                    summary = parquet_serializer.serialize_summary(
                        summary_variant_index, family_allele,
                        alternatives_data
                    )
                    effect_genes = parquet_serializer.serialize_effects(
                        family_allele, effect_data)
                    family = parquet_serializer.serialize_family(
                        family_variant_index, family_allele, genotype_data)
                    member = parquet_serializer.serialize_members(
                        family_variant_index, family_allele)

                    for (s, e, f, m) in itertools.product(
                            [summary], effect_genes, [family], member):

                        repetition += 1

                        self.data.data_append('bucket_index', bucket_index)

                        for d in (s, e, f, m):
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


class HdfsHelpers(object):

    def __init__(self, hdfs_host=None, hdfs_port=0):

        if hdfs_host is None:
            hdfs_host = "127.0.0.1"
        hdfs_host = os.getenv("DAE_HDFS_HOST", hdfs_host)
        if hdfs_port is None:
            hdfs_port = 8020
        hdfs_port = int(os.getenv("DAE_HDFS_PORT", hdfs_port))

        self.host = hdfs_host
        self.port = hdfs_port
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

    def put(self, local_filename, hdfs_filename):
        assert os.path.exists(local_filename)

        with open(local_filename, 'rb') as infile:
            self.hdfs.upload(hdfs_filename, infile)

    def get(self, hdfs_filename, local_filename):
        # assert os.path.exists(local_filename)
        assert self.exists(hdfs_filename)

        with open(local_filename, "wb") as outfile:
            self.hdfs.download(hdfs_filename, outfile)
