import os
import sys
import time
import itertools
import traceback
from box import Box

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from dae.utils.vcf_utils import GENOTYPE_TYPE
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.annotation.tools.file_io_parquet import ParquetSchema
from dae.backends.impala.serializers import ParquetSerializer


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

    ANNOTATION_EXCLUDE = [
        'effect_gene_genes',
        'effect_gene_types',
        'effect_genes',
        'effect_details_transcript_ids',
        'effect_details_details',
        'effect_details',
        'OLD_effectType',
        'OLD_effectGene',
        'OLD_effectDetails',
    ]

    def __init__(
            self, families, full_variants_iterator,
            annotation_pipeline=None,
            return_reference=True,
            return_unknown=True):

        self.families = families
        self.full_variants_iterator = full_variants_iterator
        self.return_reference = return_reference
        self.return_unknown = return_unknown

        if self.return_unknown:
            assert self.return_reference

        annotation_schema = ParquetSchema.from_arrow(
            ParquetSerializer.BASE_SCHEMA)
        if annotation_pipeline is not None:
            annotation_pipeline.collect_annotator_schema(annotation_schema)
            for schema_key in self.ANNOTATION_EXCLUDE:
                if schema_key in annotation_schema:
                    del annotation_schema[schema_key]

        self.schema = annotation_schema.to_arrow()
        self.parquet_serializer = ParquetSerializer(
            schema=annotation_schema
        )

        self.start = time.time()
        self.data = ParquetData(self.schema)

    def _setup_reference_allele(self, summary_variant, family):
        genotype = -1 * np.ones(
            shape=(2, len(family)), dtype=GENOTYPE_TYPE)

        ra = summary_variant.ref_allele
        reference_allele = FamilyAllele.from_summary_allele(
            ra, family, genotype)
        return reference_allele

    def _setup_all_unknown_allele(self, summary_variant, family):
        genotype = -1 * np.ones(
            shape=(2, len(family)), dtype=GENOTYPE_TYPE)

        ra = summary_variant.ref_allele
        unknown_allele = FamilyAllele(
            ra.chromosome,
            ra.position,
            ra.reference,
            ra.reference,
            None,  # summary_allele.summary_index,
            -1,
            ra.effect,
            {},
            family,
            genotype
        )
        return unknown_allele

    def _setup_all_unknown_variant(self, summary_variant, family_id):
        family = self.families[family_id]
        genotype = -1 * np.ones(
            shape=(2, len(family)), dtype=GENOTYPE_TYPE)
        alleles = [
            self._setup_reference_allele(summary_variant, family),
            self._setup_all_unknown_allele(summary_variant, family)
        ]
        return FamilyVariant(
            alleles, family, genotype
        )

    def _process_family_variant(
        self, bucket_index,  summary_variant_index, family_variant_index,
            family_variant):

        effect_data = \
            self.parquet_serializer.serialize_variant_effects(
                family_variant.effects
            )
        alternatives_data = family_variant.alternative
        genotype_data = \
            self.parquet_serializer.serialize_variant_genotype(
                family_variant.gt
            )
        frequency_data = \
            self.parquet_serializer.serialize_variant_frequency(
                family_variant
            )
        genomic_scores_data = \
            self.parquet_serializer.serialize_variant_genomic_scores(
                family_variant
            )

        for family_allele in family_variant.alleles:
            if family_allele.is_reference_allele and not self.return_reference:
                continue

            summary = \
                self.parquet_serializer.serialize_summary(
                    summary_variant_index, family_allele,
                    alternatives_data
                )
            frequency = \
                self.parquet_serializer.serialize_alelle_frequency(
                    family_allele, frequency_data
                )
            genomic_scores = \
                self.parquet_serializer.serialize_genomic_scores(
                    family_allele, genomic_scores_data
                )
            effect_genes = \
                self.parquet_serializer.serialize_effects(
                    family_allele, effect_data)
            family = self.parquet_serializer.serialize_family(
                family_variant_index, family_allele, genotype_data)
            member = self.parquet_serializer.serialize_members(
                family_variant_index, family_allele)

            for (s, freq, gs, e, f, m) in itertools.product(
                    [summary], [frequency], [genomic_scores],
                    effect_genes, [family], member):

                self.data.data_append('bucket_index', bucket_index)

                for d in (s, freq, gs, e, f, m):
                    for key, val in d._asdict().items():
                        self.data.data_append(key, val)

    def variants_table(self, bucket_index=0, rows=10000):

        family_variant_index = 0
        for summary_variant_index, (sumary_variant, family_variants) in \
                enumerate(self.full_variants_iterator):

            for family_variant in family_variants:
                family_variant_index += 1

                if family_variant.is_unknown():
                    if not self.return_unknown:
                        continue
                    # handle all unknown variants
                    unknown_variant = self._setup_all_unknown_variant(
                        sumary_variant, family_variant.family_id)
                    self._process_family_variant(
                        bucket_index, summary_variant_index,
                        family_variant_index,
                        unknown_variant
                    )
                else:
                    self._process_family_variant(
                        bucket_index, summary_variant_index,
                        family_variant_index,
                        family_variant)

            if family_variant_index % 1000 == 0:
                elapsed = time.time() - self.start
                print(
                    'Bucket {}: {} family variants imported for {:.2f} sec'.
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

        print('-------------------------------------------', file=sys.stderr)
        print('Bucket:', bucket_index, file=sys.stderr)
        print('-------------------------------------------', file=sys.stderr)
        elapsed = time.time() - self.start
        print(
            'DONE: {} family variants imported for {:.2f} sec'.
            format(
                family_variant_index, elapsed),
            file=sys.stderr)

    def save_variants_to_parquet(
            self, filename=None, bucket_index=1, rows=100000,
            filesystem=None):

        writer = pq.ParquetWriter(
            filename, self.data.schema,
            compression='snappy', filesystem=filesystem)

        try:
            for table in self.variants_table(
                    bucket_index=bucket_index, rows=rows):
                assert table.schema == self.data.schema
                writer.write_table(table)

        except Exception as ex:
            print('unexpected error:', ex)
            traceback.print_exc(file=sys.stdout)
        finally:
            writer.close()


class ParquetManager:

    def __init__(self, studies_dir):
        self.studies_dir = studies_dir

    def get_data_dir(self, study_id):
        return os.path.abspath(
            os.path.join(self.studies_dir, study_id, 'data')
        )

    @staticmethod
    def parquet_file_config(
            prefix, study_id=None, bucket_index=0, suffix=None):
        assert bucket_index >= 0

        basename = os.path.basename(os.path.abspath(prefix))
        if study_id is None:
            study_id = basename
        assert study_id

        if suffix is None and bucket_index == 0:
            filesuffix = ''
        elif bucket_index > 0 and suffix is None:
            filesuffix = f'_{bucket_index:0>6}'
        elif bucket_index == 0 and suffix is not None:
            filesuffix = f'{suffix}'
        else:
            filesuffix = f'_{bucket_index:0>6}{suffix}'

        variant_filename = os.path.join(
            prefix, 'variants',
            f'{study_id}_variant{filesuffix}.parquet'
        )
        pedigree_filename = os.path.join(
            prefix, 'pedigree',
            f'{study_id}_pedigree{filesuffix}.parquet'
        )

        conf = {
            'files': {
                'variant': variant_filename,
                'pedigree': pedigree_filename,
            }
        }

        return Box(conf)


def pedigree_parquet_schema():
    fields = [
        pa.field('family_id', pa.string()),
        pa.field('person_id', pa.string()),
        pa.field('dad_id', pa.string()),
        pa.field('mom_id', pa.string()),
        pa.field('sex', pa.int8()),
        pa.field('status', pa.int8()),
        pa.field('role', pa.int32()),
        pa.field('sample_id', pa.string()),
        pa.field('generated', pa.bool_()),
        pa.field('layout', pa.string()),
    ]

    return pa.schema(fields)


def add_missing_parquet_fields(pps, ped_df):
    missing_fields = set(ped_df.columns.values) - set(pps.names)

    for column in missing_fields:
        pps = pps.append(pa.field(column, pa.string()))

    return pps


def save_ped_df_to_parquet(ped_df, filename, filesystem=None):

    ped_df = ped_df.copy()
    ped_df.role = ped_df.role.apply(lambda r: r.value)
    ped_df.sex = ped_df.sex.apply(lambda s: s.value)
    ped_df.status = ped_df.status.apply(lambda s: s.value)
    if 'generated' not in ped_df:
        ped_df['generated'] = False
    if 'layout' not in ped_df:
        ped_df['layout'] = None

    pps = pedigree_parquet_schema()
    pps = add_missing_parquet_fields(pps, ped_df)

    table = pa.Table.from_pandas(ped_df, schema=pps)
    pq.write_table(table, filename, filesystem=filesystem)
