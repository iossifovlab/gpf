import os
import configparser
import glob
import pandas as pd
import pyarrow.parquet as pq
from dae.backends.raw.loader import VariantsLoader, TransmissionType
from dae.backends.impala.serializers import ParquetSerializer
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant


class ParquetLoader(VariantsLoader):
    def __init__(self, families,
                 partition_config_file, partitions_to_read=[],
                 transmission_type=TransmissionType.transmitted):
        super(ParquetLoader, self).__init__(
            families=families,
            filenames=[partition_config_file],
            source_type='parquet',
            transmission_type=transmission_type)
        self._read_partition_config(partition_config_file)
        self.root_dir = os.path.dirname(partition_config_file)
        self.partitions_to_read = partitions_to_read

    def _read_partition_config(self, config_file):
        self._config = configparser.ConfigParser()
        self._config.read(config_file)
        assert 'region_bin' in self._config
        self._file_depth = 1
        if 'family_bin' in self._config:
            self._file_depth += 1
        if 'coding_bin' in self._config:
            self._file_depth += 1
        if 'frequency_bin' in self._config:
            self._file_depth += 1

    def _get_filenames_to_open(self):
        if self.partitions_to_read == []:
            glob_path = '/'.join(['*'] * (self._file_depth + 1))
            return glob.glob(os.path.join(self.root_dir, glob_path))
        else:
            filenames = []
            for part in self.partitions_to_read:
                filenames += glob.glob(os.path.join(self.root_dir, part))

            return filenames

    def _get_bins_from_filename(self, filename):
        bins_dict = {
            'region_bin': None,
            'family_bin': None,
            'coding_bin': None,
            'frequency_bin': None,
        }

        filepath = os.path.dirname(filename)

        filepath = filepath[filepath.find('region_bin'):]

        bins = filepath.split(os.sep)
        for b in bins:
            bin_kv = tuple(b.split('='))
            bins_dict[bin_kv[0]] = bin_kv[1]

        return bins_dict

    def _table_iterator(self, table, filename):
        df = table.to_pandas()
        df = self._deserialize_fields(df)
        summary_variants_indexes = pd.unique(df['summary_variant_index'])
        for sv_index in summary_variants_indexes:
            records = []
            summary_variant_rows = df[
                df['summary_variant_index'] == sv_index
            ]
            for index, row in summary_variant_rows.iterrows():
                if any(r['allele_index'] == row['allele_index']
                        for r in records):
                    continue

                record_dict = {
                    'chrom': row['chrom'],
                    'position': row['position'],
                    'reference': row['reference'],
                    'alternative': row['alternative'],
                    'summary_variant_index':
                        row['summary_variant_index'],
                    'allele_index': row['allele_index'],
                    'allele_count': row['af_allele_count']
                }

                bins_dict = self._get_bins_from_filename(filename)

                record_dict.update(bins_dict)

                records.append(record_dict)

            summary_variant = SummaryVariantFactory. \
                summary_variant_from_records(records)

            family_variants = []
            for index, row in summary_variant_rows.iterrows():
                if row['family_variant_index'] in family_variants:
                    continue

                yield (summary_variant, row['genotype_data'])

    def _parquet_file_iterator(self, filename):
        pq_file = pq.ParquetFile(filename)
        for row_group_index in range(0, pq_file.num_row_groups):
            table = pq_file.read_row_group(row_group_index)
            for summary_variant, gt_data in self._table_iterator(
                    table,
                    filename):

                yield (summary_variant, gt_data)

    def _deserialize_fields(self, df):
        df['genotype_data'] = df['genotype_data'].apply(
                ParquetSerializer.deserialize_variant_genotype)
        df['frequency_data'] = df['frequency_data'].apply(
                ParquetSerializer.deserialize_variant_frequency)
        return df

    def full_variants_iterator(self):
        for filename in self._get_filenames_to_open():
            for summary_variant, genotype \
                    in self._parquet_file_iterator(filename):
                family_variants = []
                for fam, gt, bs in genotype.family_genotype_iterator():
                    family_variants.append(
                        FamilyVariant(summary_variant, fam, gt, bs))
                yield summary_variant, family_variants
