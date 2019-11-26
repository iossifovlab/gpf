import os
import sys
import time
import itertools
import hashlib
# import traceback
from box import Box

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import configparser

from dae.utils.vcf_utils import GENOTYPE_TYPE
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.backends.impala.serializers import ParquetSerializer


class ParquetData():

    def __init__(self, schema):
        self.schema = schema.to_arrow()
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
            field = self.schema.field(name)
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


class ParquetPartitionDescription():
    def __init__(self,
                 chromosomes,
                 region_length,
                 family_bin_size=0,
                 coding_effect_types=[],
                 rare_boundary=0):

        self.chromosomes = chromosomes
        self.region_length = region_length
        self.family_bin_size = family_bin_size
        self.coding_effect_types = coding_effect_types
        self.rare_boundary = rare_boundary

    def _evaluate_region_bin(self, family_variant):
        chromosome = family_variant.ref_allele.chromosome
        pos = family_variant.ref_allele.position // self.region_length
        if chromosome in self.chromosomes:
            return f'{chromosome}_{pos}'
        else:
            return f'other_{pos}'

    def _evaluate_family_bin(self, family_variant):
        sha256 = hashlib.sha256()
        family_variant_id = family_variant.family_id
        sha256.update(family_variant_id.encode())
        digest = int(sha256.hexdigest(), 16)
        return digest % self.family_bin_size

    def _evaluate_coding_bin(self, family_variant):
        variant_effects = set()
        for effect in family_variant.effects:
            variant_effects = variant_effects.union(effect.types)
        coding_effect_types = set(self.coding_effect_types)

        result = variant_effects.intersection(coding_effect_types)
        if len(result) == 0:
            return 0
        else:
            return 1

    def _evaluate_frequency_bin(self, family_variant):
        count = min(family_variant.get_attribute('af_allele_count'))
        frequency = min(family_variant.get_attribute('af_allele_freq'))
        if count == 1:  # Ultra rare
            frequency_bin = 1
        elif frequency < self.rare_boundary:  # Rare
            frequency_bin = 2
        else:  # Common
            frequency_bin = 3

        return frequency_bin

    def evaluate_variant_filename(self, family_variant):
        bins = (self._evaluate_region_bin(family_variant),)
        filename = f'variants_region_bin_{bins[0]}'
        if self.family_bin_size > 0:
            bins += (self._evaluate_family_bin(family_variant),)
            filename += f'_family_bin_{bins[len(bins)-1]}'
        if len(self.coding_effect_types) > 0:
            bins += (self._evaluate_coding_bin(family_variant),)
            filename += f'_coding_bin_{bins[len(bins)-1]}'
        if self.rare_boundary > 0:
            bins += (self._evaluate_frequency_bin(family_variant),)
            filename += f'_frequency_bin_{bins[len(bins)-1]}'
        filepath = os.path.join('', *tuple(map(str, bins)))
        filename += '.parquet'

        return os.path.join(filepath, filename)

    def write_partition_configuration_to_file(self, directory):
        config = configparser.ConfigParser()

        config.add_section('region_bin')
        config['region_bin']['chromosomes'] = ', '.join(self.chromosomes)
        config['region_bin']['region_length'] = str(self.region_length)

        if self.family_bin_size > 0:
            config.add_section('family_bin')
            config['family_bin']['family_bin_size'] = \
                str(self.family_bin_size)

        if len(self.coding_effect_types) > 0:
            config.add_section('coding_bin')
            config['coding_bin']['coding_effect_types'] = \
                ', '.join(self.coding_effect_types)

        if self.rare_boundary > 0:
            config.add_section('frequency_bin')
            config['frequency_bin']['rare_boundary'] = str(self.rare_boundary)

        filename = os.path.join(directory, '_PARTITION_DESCRIPTION')
        with open(filename, 'w') as configfile:
            config.write(configfile)


class ContinuousParquetFileWriter():
    """
    Class that automatically writes to a given parquet file when supplied
    enough data. Automatically dumps leftover data when closing into the file
    """
    def __init__(
                self, filepath, schema,
                filesystem=None, rows=10000):
        self._data = ParquetData(schema)
        schema = schema.to_arrow()
        path = os.path.dirname(filepath)
        if not os.path.exists(path):
            os.makedirs(path)
        self._writer = pq.ParquetWriter(
                filepath,
                schema,
                compression='snappy',
                filesystem=filesystem)
        self.rows = rows

    def _write_table(self):
        self._writer.write_table(self._data.build_table())

    def data_append(self, attributes):
        '''
        Appends the data for an entire variant to the buffer

        :param list attributes: List of key-value tuples containing the data
        '''
        for attr_name, value in attributes:
            self._data.data_append(attr_name, value)
        if len(self._data) >= self.rows:
            self._write_table()

    def close(self):
        if len(self._data) > 0:
            self._write_table()
        self._writer.close()


class VariantsParquetWriter():

    def __init__(
            self, fvars,
            partition_description,
            root_folder, bucket_index=1,
            rows=100000, include_reference=True,
            include_unknown=True, filesystem=None):

        self.fvars = fvars
        self.families = fvars.families
        self.full_variants_iterator = fvars.full_variants_iterator()

        self.include_reference = include_reference
        self.include_unknown = include_unknown

        self.bucket_index = bucket_index
        self.rows = rows
        self.filesystem = filesystem

        if self.include_unknown:
            assert self.include_unknown
        self.schema = fvars.annotation_schema
        self.parquet_serializer = ParquetSerializer(
            self.schema, include_reference=True)

        self.start = time.time()
        # self.data = ParquetData(self.schema)
        self.data_writers = {}
        self.partition_description = partition_description
        self.root_folder = root_folder

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
            {},
            family,
            genotype
        )
        return unknown_allele

    def _setup_all_unknown_variant(self, summary_variant, family_id):
        family = self.families.get_family(family_id)
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
        self, summary_variant_index, summary_variant,
            family_variant_index, family_variant):

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
            if family_allele.is_reference_allele and \
                    not self.include_reference:
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

                bin_writer = self._get_bin_writer(
                    summary_variant, family_variant)
                writer_data = []
                writer_data.append(('bucket_index', self.bucket_index))

                for d in (s, freq, gs, e, f, m):
                    for key, val in d._asdict().items():
                        writer_data.append((key, val))

                bin_writer.data_append(writer_data)

    def _get_full_filepath(self, filename):
        filepath = os.path.join(self.root_folder, filename)
        return filepath

    def _get_bin_writer(self, summary_variant, family_variant):
        filename = self.partition_description.evaluate_variant_filename(
                family_variant)

        if filename not in self.data_writers:
            filepath = self._get_full_filepath(filename)
            self.data_writers[filename] = ContinuousParquetFileWriter(
                    filepath,
                    self.schema,
                    filesystem=self.filesystem,
                    rows=self.rows)
        return self.data_writers[filename]

    def write_partition(self):
        family_variant_index = 0
        for summary_variant_index, (summary_variant, family_variants) in \
                enumerate(self.full_variants_iterator):
            for family_variant in family_variants:
                family_variant_index += 1

                if family_variant.is_unknown():
                    if not self.include_unknown:
                        continue
                    # handle all unknown variants
                    unknown_variant = self._setup_all_unknown_variant(
                        summary_variant, family_variant.family_id)
                    self._process_family_variant(
                        summary_variant_index,
                        summary_variant,
                        family_variant_index,
                        unknown_variant
                    )
                else:
                    self._process_family_variant(
                        summary_variant_index,
                        summary_variant,
                        family_variant_index,
                        family_variant)

            if family_variant_index % 1000 == 0:
                elapsed = time.time() - self.start
                print(
                    'Bucket {}: {} family variants imported for {:.2f} sec'.
                    format(
                        self.bucket_index,
                        family_variant_index, elapsed),
                    file=sys.stderr)

        for bin_writer in self.data_writers.values():
            bin_writer.close()

        print('-------------------------------------------', file=sys.stderr)
        print('Bucket:', self.bucket_index, file=sys.stderr)
        print('-------------------------------------------', file=sys.stderr)
        elapsed = time.time() - self.start
        print(
            'DONE: {} family variants imported for {:.2f} sec'.
            format(
                family_variant_index, elapsed),
            file=sys.stderr)

        self.partition_description.write_partition_configuration_to_file(
                self.root_folder)


#    def variants_table(self):
#        for key, value in self.data_writers.items():
#            yield (key, value.build_table())
#
#    def save_variants_to_parquet(
#            self, root_path):
#
#        try:
#            self.fill_bins()
#            print(self.data_writers.keys())
#            for (bins, table) in self.variants_table():
#                filename = root_path
#                filename = os.path.join(filename, *tuple(map(str, bins)))
#
#                if not os.path.exists(filename):
#                    os.makedirs(filename)
#
#                filename = os.path.join(filename,
#                                        f'variants_region_bin_{bins[0]}'
#                                        + f'_family_bin_{bins[1]}.parquet')
#                assert table.schema == self.data_writers[bins].schema
#                with pq.ParquetWriter(
#                        filename, table.schema,
#                        compression='snappy',
#                        filesystem=self.filesystem) as writer:
#                    writer.write_table(table)
#
#        except Exception as ex:
#            print('unexpected error:', ex)
#            traceback.print_exc(file=sys.stdout)


class ParquetManager:

    def __init__(self, studies_dir):
        self.studies_dir = studies_dir

    def get_data_dir(self, study_id):
        return os.path.abspath(
            os.path.join(self.studies_dir, study_id, 'data')
        )

    @staticmethod
    def build_parquet_filenames(
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
            prefix, 'variant',
            f'{study_id}_variant{filesuffix}.parquet'
        )
        pedigree_filename = os.path.join(
            prefix, 'pedigree',
            f'{study_id}_pedigree{filesuffix}.parquet'
        )

        conf = {
            'variant': variant_filename,
            'pedigree': pedigree_filename,
        }
        return Box(conf)

    @staticmethod
    def pedigree_to_parquet(fvars, pedigree_filename, filesystem=None):
        os.makedirs(
            os.path.split(pedigree_filename)[0], exist_ok=True
        )

        save_ped_df_to_parquet(
            fvars.families.ped_df, pedigree_filename,
            filesystem=filesystem
        )

    @staticmethod
    def variants_to_parquet(
            fvars, variants_filename, bucket_index=0, rows=100000,
            filesystem=None,
            include_reference=False,
            include_unknown=False):

        assert fvars.annotation_schema is not None

        os.makedirs(
            os.path.split(variants_filename)[0],
            exist_ok=True
        )

        start = time.time()

        variants_writer = VariantsParquetWriter(
            fvars,
            include_reference=include_reference,
            include_unknown=include_unknown,
            bucket_index=bucket_index,
            rows=rows,
            filesystem=filesystem
        )
        print('[DONE] going to create variants writer...')

        variants_writer.save_variants_to_parquet(
            variants_filename,
        )
        end = time.time()

        print(
            'DONE: {} for {:.2f} sec'.format(
                variants_filename, end-start),
            file=sys.stderr
        )


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
