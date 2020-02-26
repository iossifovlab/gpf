import os
import sys
import time
import itertools
import hashlib
from box import Box

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import configparser

from dae.utils.variant_utils import GENOTYPE_TYPE
from dae.variants.attributes import TransmissionType
from dae.variants.family_variant import (
    FamilyAllele,
    FamilyVariant,
    calculate_simple_best_state,
)
from dae.variants.variant import SummaryVariant, SummaryAllele
from dae.backends.impala.serializers import ParquetSerializer


class ParquetData:
    def __init__(self, schema):
        self.schema = schema.to_arrow()
        self.data_reset()

    def data_reset(self):
        self.data = {name: [] for name in self.schema.names}

    def data_append(self, attr_name, value):
        self.data[attr_name].append(value)

    def data_append_enum_array(self, attr_name, value, dtype=np.int8):
        self.data[attr_name].append(
            np.asarray([v.value for v in value if v is not None], dtype=dtype)
        )

    def data_append_str_array(self, attr_name, value):
        self.data[attr_name].append([str(v) for v in value if v is not None])

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
        return len(self.data["summary_variant_index"])


class PartitionDescriptor:
    def __init__(self):
        pass

    @property
    def chromosomes(self):
        raise NotImplementedError()

    @property
    def region_length(self):
        raise NotImplementedError()

    def variant_filename(self, family_allele):
        raise NotImplementedError()

    def write_partition_configuration(self):
        raise NotImplementedError()


class NoPartitionDescriptor(PartitionDescriptor):
    def __init__(self, output):
        super(NoPartitionDescriptor, self).__init__()
        self.output = output

    @property
    def chromosomes(self):
        return []

    @property
    def region_length(self):
        return 3_000_000_000

    def variant_filename(self, family_allele):
        return self.output

    def write_partition_configuration(self):
        return None


class ParquetPartitionDescriptor(PartitionDescriptor):
    def __init__(
        self,
        chromosomes,
        region_length,
        family_bin_size=0,
        coding_effect_types=[],
        rare_boundary=0,
        root_dirname="",
    ):

        super(ParquetPartitionDescriptor, self).__init__()
        self.output = root_dirname
        self._chromosomes = chromosomes
        self._region_length = region_length
        self._family_bin_size = family_bin_size
        self._coding_effect_types = coding_effect_types
        self._rare_boundary = rare_boundary

    @property
    def chromosomes(self):
        return self._chromosomes

    @property
    def region_length(self):
        return self._region_length

    @property
    def family_bin_size(self):
        return self._family_bin_size

    @property
    def coding_effect_types(self):
        return self._coding_effect_types

    @property
    def rare_boundary(self):
        return self._rare_boundary

    @staticmethod
    def from_config(config_path, root_dirname=""):
        assert os.path.exists(config_path), config_path

        config = configparser.ConfigParser()
        config.read(config_path)
        assert config["region_bin"] is not None

        chromosomes = list(
            map(str.strip, config["region_bin"]["chromosomes"].split(","))
        )

        region_length = int(config["region_bin"]["region_length"])
        family_bin_size = 0
        coding_effect_types = []
        rare_boundary = 0

        if "family_bin" in config:
            family_bin_size = int(config["family_bin"]["family_bin_size"])
        if "coding_bin" in config:
            coding_effect_types = config["coding_bin"]["coding_effect_types"]
            coding_effect_types = [
                et.strip() for et in coding_effect_types.split(",")
            ]
            coding_effect_types = [et for et in coding_effect_types if et]

        if "frequency_bin" in config:
            rare_boundary = int(config["frequency_bin"]["rare_boundary"])

        return ParquetPartitionDescriptor(
            chromosomes,
            region_length,
            family_bin_size,
            coding_effect_types,
            rare_boundary,
            root_dirname=root_dirname,
        )

    def _evaluate_region_bin(self, family_allele):
        chromosome = family_allele.chromosome
        pos = family_allele.position // self._region_length
        if chromosome in self._chromosomes:
            return f"{chromosome}_{pos}"
        else:
            return f"other_{pos}"

    def _family_bin_from_id(self, family_id):
        sha256 = hashlib.sha256()
        sha256.update(family_id.encode())
        digest = int(sha256.hexdigest(), 16)
        return digest % self.family_bin_size

    def _evaluate_family_bin(self, family_allele):
        return self._family_bin_from_id(family_allele.family_id)

    def _evaluate_coding_bin(self, family_allele):
        if family_allele.is_reference_allele:
            return 0
        variant_effects = set(family_allele.effect.types)
        coding_effect_types = set(self._coding_effect_types)

        result = variant_effects.intersection(coding_effect_types)
        if len(result) == 0:
            return 0
        else:
            return 1

    def _evaluate_frequency_bin(self, family_allele):
        count = family_allele.get_attribute("af_allele_count")
        frequency = family_allele.get_attribute("af_allele_freq")
        transmission_type = family_allele.transmission_type
        if transmission_type == TransmissionType.denovo:
            frequency_bin = 0
        elif count and int(count) == 1:  # Ultra rare
            frequency_bin = 1
        elif frequency and float(frequency) < self._rare_boundary:  # Rare
            frequency_bin = 2
        else:  # Common
            frequency_bin = 3

        return frequency_bin

    def variant_filename(self, family_allele):
        current_bin = self._evaluate_region_bin(family_allele)
        filepath = os.path.join(self.output, f"region_bin={current_bin}")

        filename = f"variants_region_bin_{current_bin}"
        if self._rare_boundary > 0:
            current_bin = self._evaluate_frequency_bin(family_allele)
            filepath = os.path.join(filepath, f"frequency_bin={current_bin}")
            filename += f"_frequency_bin_{current_bin}"
        if len(self._coding_effect_types) > 0:
            current_bin = self._evaluate_coding_bin(family_allele)
            filepath = os.path.join(filepath, f"coding_bin={current_bin}")
            filename += f"_coding_bin_{current_bin}"
        if self._family_bin_size > 0:
            current_bin = self._evaluate_family_bin(family_allele)
            filepath = os.path.join(filepath, f"family_bin={current_bin}")
            filename += f"_family_bin_{current_bin}"
        filename += ".parquet"

        return os.path.join(filepath, filename)

    def write_partition_configuration(self):
        config = configparser.ConfigParser()

        config.add_section("region_bin")
        config["region_bin"]["chromosomes"] = ", ".join(self._chromosomes)
        config["region_bin"]["region_length"] = str(self._region_length)

        if self._family_bin_size > 0:
            config.add_section("family_bin")
            config["family_bin"]["family_bin_size"] = str(
                self._family_bin_size
            )

        if len(self._coding_effect_types) > 0:
            config.add_section("coding_bin")
            config["coding_bin"]["coding_effect_types"] = ", ".join(
                self._coding_effect_types
            )

        if self._rare_boundary > 0:
            config.add_section("frequency_bin")
            config["frequency_bin"]["rare_boundary"] = str(self._rare_boundary)

        filename = os.path.join(self.output, "_PARTITION_DESCRIPTION")
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w") as configfile:
            config.write(configfile)

    def generate_file_access_glob(self):
        """
        Generates a glob for accessing every parquet file in the partition
        """
        glob = "*/"
        if not self.family_bin_size == 0:
            glob += "*/"
        if not self.coding_effect_types == []:
            glob += "*/"
        if not self.rare_boundary == 0:
            glob += "*/"
        glob += "*.parquet"
        return glob

    def add_family_bins_to_families(self, families):
        for family in families.values():
            family_bin = self._family_bin_from_id(family.family_id)
            for person in family.persons.values():
                person.set_attr("family_bin", family_bin)
        families._ped_df = None
        return families


class ContinuousParquetFileWriter:
    """
    Class that automatically writes to a given parquet file when supplied
    enough data. Automatically dumps leftover data when closing into the file
    """

    def __init__(self, filepath, schema, filesystem=None, rows=10000):
        self._data = ParquetData(schema)
        schema = schema.to_arrow()
        dirname = os.path.dirname(filepath)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)

        self._writer = pq.ParquetWriter(
            filepath, schema, compression="snappy", filesystem=filesystem
        )
        self.rows = rows

    def _write_table(self):
        self._writer.write_table(self._data.build_table())

    def data_append(self, attributes):
        """
        Appends the data for an entire variant to the buffer

        :param list attributes: List of key-value tuples containing the data
        """
        for attr_name, value in attributes:
            self._data.data_append(attr_name, value)
        if len(self._data) >= self.rows:
            self._write_table()

    def close(self):
        if len(self._data) > 0:
            self._write_table()
        self._writer.close()


class VariantsParquetWriter:
    def __init__(
        self,
        variants_loader,
        partition_descriptor,
        bucket_index=1,
        rows=100000,
        include_reference=True,
        include_unknown=True,
        filesystem=None,
    ):

        self.variants_loader = variants_loader
        self.families = variants_loader.families
        self.full_variants_iterator = variants_loader.full_variants_iterator()

        self.bucket_index = bucket_index
        self.rows = rows
        self.filesystem = filesystem

        self.schema = variants_loader.get_attribute("annotation_schema")
        self.parquet_serializer = ParquetSerializer(
            self.schema, include_reference=True
        )

        self.start = time.time()
        # self.data = ParquetData(self.schema)
        self.data_writers = {}
        assert isinstance(partition_descriptor, PartitionDescriptor)
        self.partition_descriptor = partition_descriptor

    def _setup_reference_allele(self, summary_variant, family):
        genotype = -1 * np.ones(shape=(2, len(family)), dtype=GENOTYPE_TYPE)
        best_state = calculate_simple_best_state(
            genotype, summary_variant.allele_count
        )

        ra = summary_variant.ref_allele
        reference_allele = FamilyAllele(ra, family, genotype, best_state)
        return reference_allele

    def _setup_all_unknown_allele(self, summary_variant, family):
        genotype = -1 * np.ones(shape=(2, len(family)), dtype=GENOTYPE_TYPE)
        best_state = calculate_simple_best_state(
            genotype, summary_variant.allele_count
        )

        ra = summary_variant.ref_allele
        unknown_allele = FamilyAllele(
            SummaryAllele(
                ra.chromosome,
                ra.position,
                ra.reference,
                ra.reference,
                None,  # summary_allele.summary_index,
                -1,
                ra.transmission_type,
                {},
            ),
            family,
            genotype,
            best_state,
        )
        return unknown_allele

    def _setup_all_unknown_variant(self, summary_variant, family_id):
        family = self.families[family_id]
        genotype = -1 * np.ones(shape=(2, len(family)), dtype=GENOTYPE_TYPE)
        alleles = [
            self._setup_reference_allele(summary_variant, family),
            self._setup_all_unknown_allele(summary_variant, family),
        ]
        best_state = -1 * np.ones(
            shape=(len(alleles), len(family)), dtype=GENOTYPE_TYPE
        )
        return FamilyVariant(
            SummaryVariant(alleles), family, genotype, best_state
        )

    def _process_family_variant(
        self,
        summary_variant_index,
        summary_variant,
        family_variant_index,
        family_variant,
    ):

        effect_data = self.parquet_serializer.serialize_variant_effects(
            family_variant.effects
        )
        alternatives_data = family_variant.alternative
        genotype_data = self.parquet_serializer.serialize_variant_genotype(
            family_variant.gt
        )
        best_state_data = self.parquet_serializer.serialize_variant_best_state(
            family_variant.best_state
        )
        genetic_model_data = family_variant.genetic_model.value

        inheritance_data = self.parquet_serializer.serialize_variant_inheritance(
            family_variant
        )

        frequency_data = self.parquet_serializer.serialize_variant_frequency(
            family_variant
        )
        genomic_scores_data = self.parquet_serializer.serialize_variant_genomic_scores(
            family_variant
        )

        for family_allele in family_variant.alleles:

            summary = self.parquet_serializer.serialize_summary(
                summary_variant_index, family_allele, alternatives_data
            )
            frequency = self.parquet_serializer.serialize_alelle_frequency(
                family_allele, frequency_data
            )
            genomic_scores = self.parquet_serializer.serialize_genomic_scores(
                family_allele, genomic_scores_data
            )
            effect_genes = self.parquet_serializer.serialize_effects(
                family_allele, effect_data
            )
            family = self.parquet_serializer.serialize_family(
                family_variant_index,
                family_allele,
                genotype_data,
                best_state_data,
                genetic_model_data,
                inheritance_data,
            )
            member = self.parquet_serializer.serialize_members(
                family_variant_index, family_allele
            )

            for (s, freq, gs, e, f, m) in itertools.product(
                [summary],
                [frequency],
                [genomic_scores],
                effect_genes,
                [family],
                member,
            ):

                writer_data = []
                writer_data.append(("bucket_index", self.bucket_index))

                for d in (s, freq, gs, e, f, m):
                    for key, val in d._asdict().items():
                        writer_data.append((key, val))

                yield (family_allele, writer_data)

    def _get_bin_writer(self, family_allele):
        filename = self.partition_descriptor.variant_filename(family_allele)

        if filename not in self.data_writers:
            self.data_writers[filename] = ContinuousParquetFileWriter(
                filename,
                self.schema,
                filesystem=self.filesystem,
                rows=self.rows,
            )
        return self.data_writers[filename]

    def _write_internal(self):
        family_variant_index = 0
        for (
            summary_variant_index,
            (summary_variant, family_variants),
        ) in enumerate(self.full_variants_iterator):
            for family_variant in family_variants:
                family_variant_index += 1

                fv = family_variant
                if family_variant.is_unknown():
                    # handle all unknown variants
                    unknown_variant = self._setup_all_unknown_variant(
                        summary_variant, family_variant.family_id
                    )
                    fv = unknown_variant

                data_gen = self._process_family_variant(
                    summary_variant_index,
                    summary_variant,
                    family_variant_index,
                    fv,
                )

                for (family_allele, data) in data_gen:
                    bin_writer = self._get_bin_writer(family_allele)
                    bin_writer.data_append(data)

            if family_variant_index % 1000 == 0:
                elapsed = time.time() - self.start
                print(
                    "Bucket {}; {}:{}: "
                    "{} family variants imported for {:.2f} sec".format(
                        self.bucket_index,
                        summary_variant.chromosome,
                        summary_variant.position,
                        family_variant_index,
                        elapsed,
                    ),
                    file=sys.stderr,
                )

        filenames = list(self.data_writers.keys())

        for bin_writer in self.data_writers.values():
            bin_writer.close()

        print("-------------------------------------------", file=sys.stderr)
        print("Bucket:", self.bucket_index, file=sys.stderr)
        print("-------------------------------------------", file=sys.stderr)
        elapsed = time.time() - self.start
        print(
            "DONE: {} family variants imported for {:.2f} sec".format(
                family_variant_index, elapsed
            ),
            file=sys.stderr,
        )

        return filenames

    def write_dataset(self):
        filenames = self._write_internal()

        self.partition_descriptor.write_partition_configuration()
        return filenames


class ParquetManager:
    @staticmethod
    def build_parquet_filenames(
        prefix, study_id=None, bucket_index=0, suffix=None
    ):
        assert bucket_index >= 0

        basename = os.path.basename(os.path.abspath(prefix))
        if study_id is None:
            study_id = basename
        assert study_id

        if suffix is None and bucket_index == 0:
            filesuffix = ""
        elif bucket_index > 0 and suffix is None:
            filesuffix = f"_{bucket_index:0>6}"
        elif bucket_index == 0 and suffix is not None:
            filesuffix = f"{suffix}"
        else:
            filesuffix = f"_{bucket_index:0>6}{suffix}"

        variant_filename = os.path.join(
            prefix, "variant", f"{study_id}_variant{filesuffix}.parquet"
        )
        pedigree_filename = os.path.join(
            prefix, "pedigree", f"{study_id}_pedigree{filesuffix}.parquet"
        )
        conf = {
            "variant": variant_filename,
            "pedigree": pedigree_filename,
        }

        return Box(conf, default_box=True)

    @staticmethod
    def families_to_parquet(families, pedigree_filename):

        dirname = os.path.dirname(pedigree_filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        save_ped_df_to_parquet(families.ped_df, pedigree_filename)

    @staticmethod
    def variants_to_parquet_filename(
        variants_loader, variants_filename, bucket_index=0, rows=100000
    ):

        assert variants_loader.annotation_schema is not None

        dirname = os.path.dirname(variants_filename)
        os.makedirs(dirname, exist_ok=True)

        start = time.time()
        partition_descriptor = NoPartitionDescriptor(variants_filename)

        variants_writer = VariantsParquetWriter(
            variants_loader,
            partition_descriptor,
            bucket_index=bucket_index,
            rows=rows,
        )

        variants_writer.write_dataset()
        end = time.time()

        print(
            "DONE: {} for {:.2f} sec".format(variants_filename, end - start),
            file=sys.stderr,
        )

    @staticmethod
    def variants_to_parquet_partition(
        variants_loader, partition_descriptor, bucket_index=1, rows=100000
    ):

        assert variants_loader.get_attribute("annotation_schema") is not None

        start = time.time()

        variants_writer = VariantsParquetWriter(
            variants_loader,
            partition_descriptor,
            bucket_index=bucket_index,
            rows=rows,
        )

        variants_writer.write_dataset()
        elapsed = time.time() - start

        print(f"DONE: for {elapsed:.2f} sec", file=sys.stderr)


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
        pa.field("generated", pa.bool_()),
        pa.field("layout", pa.string()),
    ]

    return pa.schema(fields)


def add_missing_parquet_fields(pps, ped_df):
    missing_fields = set(ped_df.columns.values) - set(pps.names)

    if "family_bin" in missing_fields:
        pps = pps.append(pa.field("family_bin", pa.int8()))
        missing_fields = missing_fields - set(["family_bin"])

    rename = {}
    for column in missing_fields:
        name = column.lower().replace(".", "_")
        pps = pps.append(pa.field(name, pa.string()))
        rename[column] = name

    ped_df = ped_df.rename(columns=rename)
    missing_fields = [rename[col] for col in missing_fields]

    for column in missing_fields:
        ped_df[column] = ped_df[column].apply(lambda v: str(v))

    return ped_df, pps


def save_ped_df_to_parquet(ped_df, filename, filesystem=None):
    ped_df = ped_df.copy()

    ped_df.role = ped_df.role.apply(lambda r: r.value)
    ped_df.sex = ped_df.sex.apply(lambda s: s.value)
    ped_df.status = ped_df.status.apply(lambda s: s.value)
    if "generated" not in ped_df:
        ped_df["generated"] = False
    if "layout" not in ped_df:
        ped_df["layout"] = None

    pps = pedigree_parquet_schema()
    ped_df, pps = add_missing_parquet_fields(pps, ped_df)

    table = pa.Table.from_pandas(ped_df, schema=pps)
    pq.write_table(table, filename, filesystem=filesystem)
