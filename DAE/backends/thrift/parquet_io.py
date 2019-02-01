'''
Created on May 30, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

from builtins import str
import sys
import traceback

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

# from tqdm import tqdm

from variants.attributes import Role, Sex, Status
from annotation.tools.file_io_parquet import ParquetSchema


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

    def build_writer(self, filename):
        writer = pq.ParquetWriter(filename, self.schema)
        return writer

    def __len__(self):
        return len(self.data['summary_variant_index'])


class VariantsParquetWriter(object):

    SUMMARY_SCHEMA = pa.schema([
        pa.field("bucket_index", pa.int32()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int16()),
        pa.field("allele_count", pa.int16()),
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int64()),
        pa.field("reference", pa.string()),
        pa.field("alternative", pa.string()),
        pa.field("variant_type", pa.int8()),
        pa.field("cshl_variant", pa.string()),
        pa.field("cshl_position", pa.int64()),
        pa.field("effect_type", pa.string()),
        pa.field("effect_gene_genes", pa.list_(pa.string())),
        pa.field("effect_gene_types", pa.list_(pa.string())),
        pa.field("effect_details_transcript_ids", pa.list_(pa.string())),
        pa.field("effect_details_details", pa.list_(pa.string())),
        pa.field("af_parents_called_count", pa.int32()),
        pa.field("af_parents_called_percent", pa.float64()),
        pa.field("af_allele_count", pa.int32()),
        pa.field("af_allele_freq", pa.float64()),
        pa.field("transmission_type", pa.string()),
    ])

    EFFECT_GENE_SCHEMA = pa.schema([
        pa.field("bucket_index", pa.int32()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int16()),
        pa.field("effect_gene_index", pa.int8()),
        pa.field("effect_type", pa.string()),
        pa.field("effect_gene", pa.string()),
    ])

    FAMILY_SCHEMA = pa.schema([
        pa.field("bucket_index", pa.int32()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int8()),
        pa.field("family_variant_index", pa.int64()),
        pa.field("family_id", pa.string()),
        pa.field("genotype", pa.list_(pa.int8())),
        pa.field("inheritance_in_members", pa.list_(pa.int8())),
        pa.field("variant_in_members", pa.list_(pa.string())),
        pa.field("variant_in_roles", pa.list_(pa.int8())),
        pa.field("variant_in_sexes", pa.list_(pa.int8())),
    ])

    MEMBER_SCHEMA = pa.schema([
        pa.field("bucket_index", pa.int32()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int8()),
        pa.field("family_variant_index", pa.int64()),

        pa.field("member_variant", pa.string()),
    ])

    def __init__(self, full_variants_iterator, annotation_schema=None):
        self.full_variants_iterator = full_variants_iterator

        if annotation_schema is not None:
            base_schema = ParquetSchema.from_arrow(self.SUMMARY_SCHEMA)
            summary_schema = ParquetSchema.merge_schemas(
                base_schema, annotation_schema).to_arrow()
        else:
            summary_schema = self.SUMMARY_SCHEMA

        self.summary_data = ParquetData(summary_schema)

        self.effect_gene_data = ParquetData(self.EFFECT_GENE_SCHEMA)

        self.family_data = ParquetData(self.FAMILY_SCHEMA)
        self.member_data = ParquetData(self.MEMBER_SCHEMA)

    def _family_allele_to_data(
            self, fv, fa,
            bucket_index, summary_index, family_variant_index):

        self.family_data.data_append("bucket_index", bucket_index)
        self.family_data.data_append("summary_variant_index", summary_index)
        self.family_data.data_append("allele_index", fa.allele_index)
        self.family_data.data_append(
            "family_variant_index", family_variant_index)

        self.family_data.data_append("family_id", fa.family_id)

        self.family_data.data_append("genotype", fv.gt_flatten())
        self.family_data.data_append_enum_array(
            "inheritance_in_members",
            set(fa.inheritance_in_members))
        self.family_data.data_append_str_array(
            "variant_in_members",
            fa.variant_in_members)
        self.family_data.data_append_enum_array(
            "variant_in_roles",
            set(fa.variant_in_roles))
        self.family_data.data_append_enum_array(
            "variant_in_sexes",
            set(fa.variant_in_sexes))

        assert len(fa.inheritance_in_members) == len(fa.members_ids)
        assert len(fa.variant_in_members) == len(fa.members_ids)
        assert len(fa.variant_in_roles) == len(fa.members_ids)
        assert len(fa.variant_in_sexes) == len(fa.members_ids)

        for member_index, member_id in enumerate(fa.members_ids):
            if fa.variant_in_members[member_index] is None:
                continue

            self.member_data.data_append("bucket_index", bucket_index)
            self.member_data.data_append(
                "summary_variant_index", summary_index)
            self.member_data.data_append("allele_index", fa.allele_index)
            self.member_data.data_append(
                "family_variant_index", family_variant_index)
            self.member_data.data_append(
                "member_variant",
                fa.variant_in_members[member_index])

    def variants_table(self, bucket_index=0, batch_size=200000):
        family_variant_index = 0

        for summary_variant_index, (summary_variant, family_variants) in \
                enumerate(self.full_variants_iterator):

            for sa in summary_variant.alleles:
                sa.attributes['bucket_index'] = bucket_index
                for name in self.summary_data.schema.names:
                    self.summary_data.data_append(name, sa.get_attribute(name))
                if sa.is_reference_allele:
                    continue
                for effect_gene_index, effect_gene in \
                        enumerate(sa.effects.genes):

                    self.effect_gene_data.data_append(
                        "bucket_index", bucket_index)
                    self.effect_gene_data.data_append(
                        "summary_variant_index", summary_variant_index)
                    self.effect_gene_data.data_append(
                        "allele_index", sa.allele_index)
                    self.effect_gene_data.data_append(
                        "effect_gene_index", effect_gene_index)
                    self.effect_gene_data.data_append(
                        "effect_type", effect_gene.effect)
                    self.effect_gene_data.data_append(
                        "effect_gene", effect_gene.symbol)

            for fv in family_variants:
                for allele in fv.alleles:
                    self._family_allele_to_data(
                        fv, allele,
                        bucket_index, summary_variant_index,
                        family_variant_index)
                    family_variant_index += 1

            if len(self.family_data) >= batch_size:

                family_table = self.family_data.build_table()
                member_table = self.member_data.build_table()
                summary_table = self.summary_data.build_table()
                effect_gene_table = self.effect_gene_data.build_table()

                yield summary_table, effect_gene_table, \
                    family_table, member_table

        if len(self.family_data) > 0:
            family_table = self.family_data.build_table()
            member_table = self.member_data.build_table()
            summary_table = self.summary_data.build_table()
            effect_gene_table = self.effect_gene_data.build_table()

            yield summary_table, effect_gene_table, \
                family_table, member_table

    def save_variants_to_parquet(
            self,
            summary_filename=None, effect_gene_filename=None,
            family_filename=None, member_filename=None,
            bucket_index=1, batch_size=100000):

        family_writer = self.family_data.build_writer(family_filename)
        member_writer = self.member_data.build_writer(member_filename)
        summary_writer = self.summary_data.build_writer(
            summary_filename)
        effect_gene_writer = self.effect_gene_data.build_writer(
            effect_gene_filename)

        try:
            for stable, etable, ftable, mtable in self.variants_table(
                    bucket_index, batch_size):
                assert ftable.schema == self.family_data.schema
                family_writer.write_table(ftable)
                assert mtable.schema == self.member_data.schema
                member_writer.write_table(mtable)

                assert stable.schema == self.summary_data.schema
                summary_writer.write_table(stable)
                assert etable.schema == self.effect_gene_data.schema
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
    ped_df.status = ped_df.status.apply(lambda s: s.value)

    table = pa.Table.from_pandas(ped_df, schema=pedigree_parquet_schema())
    pq.write_table(table, filename)


def read_ped_df_from_parquet(filename):
    ped_df = pd.read_parquet(filename, engine="pyarrow")
    ped_df.role = ped_df.role.apply(lambda v: Role(v))
    ped_df.sex = ped_df.sex.apply(lambda v: Sex(v))
    ped_df.status = ped_df.status.apply(lambda v: Status(v))
    if 'layout' in ped_df:
        ped_df.layout = ped_df.layout.apply(lambda v: v.split(':')[-1])

    return ped_df
