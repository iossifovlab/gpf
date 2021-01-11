import os
import sys
import time
import re
import hashlib
import itertools
import logging

import toml
from box import Box

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import configparser

from dae.utils.variant_utils import GENOTYPE_TYPE
from dae.variants.attributes import TransmissionType
from dae.variants.family_variant import FamilyAllele, FamilyVariant, \
    calculate_simple_best_state
from dae.variants.variant import SummaryVariant, SummaryAllele
from dae.backends.impala.serializers import AlleleParquetSerializer


logger = logging.getLogger(__name__)


class PartitionDescriptor:
    def __init__(self):
        pass

    def has_partitions(self):
        raise NotImplementedError()

    def build_impala_partitions(self):
        raise NotImplementedError()

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
    def __init__(self, root_dirname=""):
        super(NoPartitionDescriptor, self).__init__()
        self.output = root_dirname

    def has_partitions(self):
        return False

    @property
    def chromosomes(self):
        return []

    @property
    def region_length(self):
        return 3_000_000_000

    def variant_filename(self, family_allele):
        bucket_index = family_allele.get_attribute("bucket_index")
        filename = f"nopart_{bucket_index:0>6}_variants.parquet"
        return os.path.join(self.output, filename)

    def write_partition_configuration(self):
        return None

    def generate_file_access_glob(self):
        """
        Generates a glob for accessing every parquet file in the partition
        """
        return "*variants.parquet"

    def variants_filename_basedir(self, filename):
        regexp = re.compile(
            "^(?P<basedir>.+)/(?P<prefix>.+)variants.parquet$")
        match = regexp.match(filename)
        if not match:
            return None

        assert "basedir" in match.groupdict()
        basedir = match.groupdict()["basedir"]
        if basedir and basedir[-1] != "/":
            basedir += "/"
        return basedir


class ParquetPartitionDescriptor(PartitionDescriptor):
    def __init__(
            self,
            chromosomes,
            region_length,
            family_bin_size=0,
            coding_effect_types=[],
            rare_boundary=0,
            root_dirname=""):

        super(ParquetPartitionDescriptor, self).__init__()
        self.output = root_dirname
        self._chromosomes = chromosomes
        self._region_length = region_length
        self._family_bin_size = family_bin_size
        self._coding_effect_types = coding_effect_types
        self._rare_boundary = rare_boundary

    def has_partitions(self):
        return True

    def build_impala_partitions(self):
        partitions = ["region_bin string"]

        if not self.rare_boundary <= 0:
            partitions.append("frequency_bin tinyint")
        if not self.coding_effect_types == []:
            partitions.append("coding_bin tinyint")
        if not self.family_bin_size <= 0:
            partitions.append("family_bin tinyint")

        return ", ".join(partitions)

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

    def _variants_partition_bins(self):
        partition_bins = []
        region_bins = [
            ("region_bin", f"{chrom}_0") for chrom in self._chromosomes
        ]
        partition_bins.append(region_bins)

        if self._rare_boundary > 0:
            frequency_bins = [
                ("frequency_bin", "1"),
                ("frequency_bin", "2"),
                ("frequency_bin", "3")
            ]
            partition_bins.append(frequency_bins)
        if len(self._coding_effect_types) > 0:
            coding_bins = [
                ("coding_bin", "0"),
                ("coding_bin", "1")
            ]
            partition_bins.append(coding_bins)
        if self._family_bin_size > 0:
            family_bins = [
                ("family_bin", f"{fb}")
                for fb in range(self._family_bin_size)
            ]
            partition_bins.append(family_bins)
        return partition_bins

    def _variants_filenames_regexp(self):
        partition_bins = self._variants_partition_bins()
        product = next(itertools.product(*partition_bins))
        dirname_parts = [
            f"{p[0]}=(?P<{p[0]}>.+)" for p in product
        ]
        filename_parts = [
            f"{p[0]}_(?P={p[0]})" for p in product
        ]
        dirname = "/".join(dirname_parts)
        dirname = os.path.join("^(?P<basedir>.+)", dirname)
        filename = "_".join(filename_parts)
        filename = f"variants_{filename}\\.parquet$"

        filename = os.path.join(dirname, filename)
        return re.compile(filename, re.VERBOSE)

    def variants_filename_basedir(self, filename):
        regexp = self._variants_filenames_regexp()
        match = regexp.match(filename)
        if not match:
            return None

        assert "basedir" in match.groupdict()
        basedir = match.groupdict()["basedir"]
        if basedir and basedir[-1] != "/":
            basedir += "/"
        return basedir

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

    def __init__(
            self, filepath, variant_loader, filesystem=None, rows=100_000):

        self.filepath = filepath
        annotation_schema = variant_loader.get_attribute("annotation_schema")
        extra_attributes = variant_loader.get_attribute("extra_attributes")
        self.serializer = AlleleParquetSerializer(
            annotation_schema, extra_attributes)
        self.schema = self.serializer.schema

        dirname = os.path.dirname(filepath)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        self.dirname = dirname

        self._writer = pq.ParquetWriter(
            filepath, self.schema, compression="snappy", filesystem=filesystem
        )
        self.rows = rows
        self._data = None
        self.data_reset()

    def data_reset(self):
        self._data = {name: [] for name in self.schema.names}

    def size(self):
        return len(self._data["chromosome"])

    def build_table(self):
        table = pa.Table.from_pydict(self._data, self.schema)
        return table

    def _write_table(self):
        self._writer.write_table(self.build_table())
        self.data_reset()

    def append_allele(self, variant_data, extra_attributes_data, allele):
        """
        Appends the data for an entire variant to the buffer

        :param list attributes: List of key-value tuples containing the data
        """
        data = self.serializer.build_allele_batch_dict(
            variant_data, extra_attributes_data, allele)
        for k, v in self._data.items():
            v.extend(data[k])

        if self.size() >= self.rows:
            logger.info(
                f"parquet writer {self.filepath} data flushing "
                f"at len {self.size()}")
            self._write_table()

    def close(self):
        logger.info(
            f"closing parquet writer {self.dirname} "
            f"at len {self.size()}")

        if self.size() > 0:
            self._write_table()
        self._writer.close()


class VariantsParquetWriter:
    def __init__(
            self,
            variants_loader,
            partition_descriptor,
            bucket_index=1,
            rows=100_000,
            include_reference=True,
            filesystem=None):

        self.variants_loader = variants_loader
        self.families = variants_loader.families
        self.full_variants_iterator = variants_loader.full_variants_iterator()

        self.bucket_index = bucket_index
        self.rows = rows
        self.filesystem = filesystem

        self.include_reference = include_reference

        self.start = time.time()
        self.data_writers = {}
        assert isinstance(partition_descriptor, PartitionDescriptor)
        self.partition_descriptor = partition_descriptor

        annotation_schema = self.variants_loader.get_attribute(
            "annotation_schema")
        extra_attributes = self.variants_loader.get_attribute(
            "extra_attributes")
        self.serializer = AlleleParquetSerializer(
            annotation_schema, extra_attributes)

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
                summary_index=ra.summary_index,
                allele_index=-1,
                transmission_type=ra.transmission_type,
                attributes={},
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

    def _get_bin_writer(self, family_allele):
        filename = self.partition_descriptor.variant_filename(family_allele)

        if filename not in self.data_writers:
            self.data_writers[filename] = ContinuousParquetFileWriter(
                filename,
                self.variants_loader,
                filesystem=self.filesystem,
                rows=self.rows,
            )
        return self.data_writers[filename]

    def _write_internal(self):
        family_variant_index = 0
        report = False

        for summary_variant_index, (summary_variant, family_variants) in \
                enumerate(self.full_variants_iterator):

            summary_alleles = summary_variant.alt_alleles
            if self.include_reference:
                summary_alleles = summary_variant.alleles

            summary_blobs = self.serializer.serialize_summary_data(
                summary_alleles
            )

            scores_blob = self.serializer.serialize_scores_data(
                summary_alleles)

            for family_variant in family_variants:
                family_variant_index += 1

                fv = family_variant
                if family_variant.is_unknown():
                    # handle all unknown variants
                    unknown_variant = self._setup_all_unknown_variant(
                        summary_variant, family_variant.family_id
                    )
                    fv = unknown_variant

                fv.summary_index = summary_variant_index
                fv.family_index = family_variant_index

                for family_allele in fv.alleles:
                    extra_atts = {
                        "bucket_index": self.bucket_index,
                        "family_index": family_variant_index
                    }
                    family_allele.update_attributes(extra_atts)

                alleles = fv.alt_alleles
                if self.include_reference or fv.is_reference():
                    alleles = fv.alleles

                variant_data = self.serializer.serialize_family_variant(
                    alleles, summary_blobs, scores_blob)
                extra_attributes_data = \
                    self.serializer.serialize_extra_attributes(fv)
                for family_allele in alleles:
                    bin_writer = self._get_bin_writer(family_allele)
                    bin_writer.append_allele(
                        variant_data, extra_attributes_data, family_allele)

            if summary_variant_index % 1000 == 0:
                report = True

            if report:
                elapsed = time.time() - self.start
                print(
                    f"Bucket {self.bucket_index}; "
                    f"{summary_variant.chromosome}:"
                    f"{summary_variant.position}: "
                    f"{summary_variant_index}/"
                    f"{family_variant_index} variants imported "
                    f"for {elapsed:.2f} sec ({len(self.data_writers)} files)",
                    file=sys.stderr,
                )
                report = False

        filenames = list(self.data_writers.keys())

        for bin_writer in self.data_writers.values():
            bin_writer.close()

        print("-------------------------------------------", file=sys.stderr)
        print("Bucket:", self.bucket_index, file=sys.stderr)
        print("-------------------------------------------", file=sys.stderr)
        elapsed = time.time() - self.start
        print(
            f"DONE: {family_variant_index} family variants imported "
            f"for {elapsed:.2f} sec ({len(self.data_writers)} files)",
            file=sys.stderr,
        )
        print("-------------------------------------------", file=sys.stderr)

        return filenames

    def write_schema(self):
        config = dict()

        schema = self.serializer.schema
        config["variants_schema"] = {}
        for k in schema.names:
            v = schema.field(k)
            config["variants_schema"][k] = str(v.type)

        schema = self.serializer.describe_blob_schema()
        config["blob"] = {}
        for k, v in schema.items():
            config["blob"][k] = v

        if os.path.isdir(self.partition_descriptor.output):
            path = self.partition_descriptor.output
        else:
            path = os.path.dirname(self.partition_descriptor.output)
        filename = os.path.join(path, "_VARIANTS_SCHEMA")

        config["extra_attributes"] = {}
        extra_attributes = self.serializer.extra_attributes
        for attr in extra_attributes:
            config["extra_attributes"][attr] = "string"

        with open(filename, "w") as configfile:
            content = toml.dumps(config)
            configfile.write(content)

    def write_dataset(self):
        filenames = self._write_internal()

        self.partition_descriptor.write_partition_configuration()
        self.write_schema()

        return filenames


class ParquetManager:
    @staticmethod
    def build_parquet_filenames(
            prefix, study_id=None, bucket_index=0, suffix=None):

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

        variants_dirname = os.path.join(prefix, "variants")
        variant_filename = os.path.join(
            variants_dirname, f"{study_id}{filesuffix}_variants.parquet")

        pedigree_filename = os.path.join(
            prefix, "pedigree", f"{study_id}{filesuffix}_pedigree.parquet")

        conf = {
            "variants_dirname": variants_dirname,
            "variants": variant_filename,
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
    def variants_to_parquet(
            variants_loader, partition_descriptor,
            bucket_index=1, rows=100_000, include_reference=False):

        assert variants_loader.get_attribute("annotation_schema") is not None
        print(f"variants to parquet ({rows} rows)", file=sys.stderr)

        start = time.time()

        variants_writer = VariantsParquetWriter(
            variants_loader,
            partition_descriptor,
            bucket_index=bucket_index,
            rows=rows,
            include_reference=include_reference)

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
