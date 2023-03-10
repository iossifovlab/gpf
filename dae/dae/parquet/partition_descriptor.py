from __future__ import annotations
import math
import textwrap
import hashlib
import pathlib
import configparser

from typing import Optional, List, Iterable, Set, Tuple, Union, Dict, Any

import yaml
import jinja2

from dae.variants.attributes import TransmissionType
from dae.utils import fs_utils


class PartitionDescriptor:
    """Class to represent partition of a genotype dataset."""

    # pylint: disable=too-many-public-methods
    def __init__(
            self,
            chromosomes: Optional[List[str]] = None,
            region_length: int = 0,
            family_bin_size: int = 0,
            coding_effect_types: Optional[List[str]] = None,
            rare_boundary: float = 0):
        if chromosomes is None:
            self.chromosomes: List[str] = []
        else:
            self.chromosomes = chromosomes
        self.region_length = region_length
        self.family_bin_size = family_bin_size
        self.coding_effect_types: Set[str] = \
            set(coding_effect_types) if coding_effect_types else set()
        self.rare_boundary = rare_boundary

    @staticmethod
    def _configparser_parse(content: str):
        parser = configparser.ConfigParser()
        parser.read_string(content)
        return parser

    @staticmethod
    def parse(path_name: Union[pathlib.Path, str]) -> PartitionDescriptor:
        """Parse partition description from a file.

        When the file name has a `.conf` suffix or is without suffix the format
        of the file is assumed to be python config file and it is parsed
        using the Python ConfigParser class.

        When the file name has `.yaml` suffix the file is parsed using the
        YAML parser.
        """
        if isinstance(path_name, str):
            path_name = pathlib.Path(path_name)
        if path_name.suffix in {"", ".conf"}:
            # parse configparser content
            with open(path_name, "r", encoding="utf8") as infile:
                return PartitionDescriptor.parse_string(infile.read(), "conf")
        elif path_name.suffix == ".yaml":
            # parse YAML content
            with open(path_name, "r", encoding="utf8") as infile:
                return PartitionDescriptor.parse_string(infile.read(), "yaml")
        else:
            raise ValueError(
                f"unsupported partition description format "
                f"<{path_name.suffix}>")

    @staticmethod
    def parse_string(
            content: str,
            content_format: str = "conf") -> PartitionDescriptor:
        """Parse partition description from a string.

        The supported formats are the Python config format and YAML. Example
        string content should be as follows.

        Example Python config format:
        ```
        [region_bin]
        chromosomes = chr1, chr2
        region_length = 10
        [frequency_bin]
        rare_boundary = 5.0
        [coding_bin]
        coding_effect_types = frame-shift,splice-site,nonsense,missense
        [family_bin]
        family_bin_size=10
        ```

        Example YAML format:
        ```
        region_bin:
            chromosomes: chr1, chr2
            region_length: 10
        frequency_bin:
            rare_boundary: 5.0
        coding_bin:
            coding_effect_types: frame-shift,splice-site,nonsense,missense
        family_bin:
            family_bin_size: 10
        ```
        """
        content = content.strip()
        if not content:
            return PartitionDescriptor()
        if content_format == "conf":
            parsed_data = PartitionDescriptor._configparser_parse(content)
        elif content_format == "yaml":
            parsed_data = yaml.safe_load(content)
        else:
            raise ValueError(
                f"unsuported partition description format <{content_format}>")

        return PartitionDescriptor.parse_dict(parsed_data)

    @staticmethod
    def parse_dict(config_dict) -> PartitionDescriptor:
        """Parse configuration dictionary and create a partion descriptor."""
        config: Dict[str, Any] = {}
        if "region_bin" in config_dict.keys():
            config["region_length"] = int(
                config_dict["region_bin"]["region_length"])
            config["chromosomes"] = [
                c.strip()
                for c in config_dict["region_bin"]["chromosomes"].split(",")]

        if "family_bin" in config_dict.keys():
            config["family_bin_size"] = int(
                config_dict["family_bin"]["family_bin_size"])

        if "frequency_bin" in config_dict.keys():
            config["rare_boundary"] = float(
                config_dict["frequency_bin"]["rare_boundary"])

        if "coding_bin" in config_dict.keys():
            config["coding_effect_types"] = set(
                s.strip()
                for s in config_dict["coding_bin"][
                    "coding_effect_types"
                ].split(",")
            )
        return PartitionDescriptor(
            chromosomes=config.get("chromosomes"),
            region_length=config.get("region_length", 0),
            family_bin_size=config.get("family_bin_size", 0),
            rare_boundary=config.get("rare_boundary", 0.0),
            coding_effect_types=config.get("coding_effect_types")
        )

    def has_region_bins(self) -> bool:
        return len(self.chromosomes) > 0 and self.region_length > 0

    def has_family_bins(self) -> bool:
        return self.family_bin_size > 0

    def has_coding_bins(self) -> bool:
        return len(self.coding_effect_types) > 0

    def has_frequency_bins(self) -> bool:
        return self.rare_boundary > 0

    def has_summary_partitions(self) -> bool:
        """Check if partition applicable to summary allele are defined."""
        return self.has_region_bins() or self.has_frequency_bins() or \
            self.has_coding_bins()

    def has_family_partitions(self) -> bool:
        """Check if partition applicable to family allele are defined."""
        return self.has_region_bins() or self.has_frequency_bins() or \
            self.has_coding_bins() or self.has_family_bins()

    def has_partitions(self) -> bool:
        """Equivalent to `has_family_partitions` method."""
        return self.has_family_partitions()

    def make_region_bin(self, chrom: str, pos: int) -> str:
        """Produce region bin for given chromosome and position."""
        if not self.has_region_bins():
            raise ValueError(
                f"Partition <{self.serialize()}> does not define region bins.")
        assert self.chromosomes is not None
        assert self.region_length > 0

        pos_bin = pos // self.region_length
        if chrom in self.chromosomes:
            return f"{chrom}_{pos_bin}"

        return f"other_{pos_bin}"

    def make_family_bin(self, family_id: str) -> int:
        """Produce family bin for given family ID."""
        if not self.has_family_bins():
            raise ValueError(
                f"Partition <{self.serialize()}> does not define family bins.")
        sha256 = hashlib.sha256()
        sha256.update(family_id.encode())
        digest = int(sha256.hexdigest(), 16)
        return int(digest % self.family_bin_size)

    def make_coding_bin(self, effect_types: Iterable[str]) -> int:
        """Produce coding bin for given list of effect types."""
        if not self.has_coding_bins():
            raise ValueError(
                f"Partition <{self.serialize()}> does not define coding bins.")
        variant_effects = set(effect_types)

        result = variant_effects.intersection(self.coding_effect_types)
        if len(result) == 0:
            return 0
        return 1

    def make_frequency_bin(
            self, allele_count: Optional[int], allele_freq: Optional[float],
            is_denovo: bool = False):
        """Produce frequency bin from allele count, frequency and de Novo flag.

        Params are allele count, allele frequence and de Novo flag.
        """
        if is_denovo:
            frequency_bin = 0
        elif allele_count and int(allele_count) == 1:  # Ultra rare
            frequency_bin = 1
        elif allele_freq and float(allele_freq) < self.rare_boundary:  # Rare
            frequency_bin = 2
        else:  # Common
            frequency_bin = 3

        return frequency_bin

    def dataset_summary_partition(self) -> List[Tuple[str, str]]:
        """Build summary parquet dataset partition for table creation.

        When creating an Impala or BigQuery table it is helpful to have
        the list of partitions and types used in the parquet dataset.
        """
        result = []
        if self.has_region_bins():
            result.append(("region_bin", "string"))
        if self.has_frequency_bins():
            result.append(("frequency_bin", "int8"))
        if self.has_coding_bins():
            result.append(("coding_bin", "int8"))
        return result

    def dataset_family_partition(self) -> List[Tuple[str, str]]:
        """Build family dataset partition for table creation.

        When creating an Impala or BigQuery table it is helpful to have
        the list of partitions and types used in the parquet dataset.
        """
        result = self.dataset_summary_partition()
        if self.has_family_bins():
            result.append(("family_bin", "int8"))
        return result

    def summary_partition(self, allele) -> List[Tuple[str, str]]:
        """Produce summary partition for an allele.

        The partition is returned as a list of tuples consiting of the
        name of the partition and the value.

        Example:
        [
            ("region_bin", "chr1_0"),
            ("frequency_bin", "0"),
            ("coding_bin", "1"),
        ]
        """
        result = []
        if self.has_region_bins():
            result.append((
                "region_bin",
                self.make_region_bin(allele.chrom, allele.position)))
        if self.has_frequency_bins():
            allele_count = allele.get_attribute("af_allele_count")
            allele_freq = allele.get_attribute("af_allele_freq")
            is_denovo = allele.transmission_type == TransmissionType.denovo
            result.append((
                "frequency_bin",
                self.make_frequency_bin(
                    allele_count=allele_count,
                    allele_freq=allele_freq,
                    is_denovo=is_denovo)
            ))
        if self.has_coding_bins():
            coding_bin = 0
            if allele.is_reference_allele:
                coding_bin = 0
            else:
                coding_bin = self.make_coding_bin(allele.effect_types)
            result.append(("coding_bin", str(coding_bin)))

        return result

    def family_partition(self, allele) -> List[Tuple[str, str]]:
        """Produce family partition for an allele.

        The partition is returned as a list of tuples consiting of the
        name of the partition and the value.

        Example:
        [
            ("region_bin", "chr1_0"),
            ("frequency_bin", "0"),
            ("coding_bin", "1"),
            ("family_bin", "1)
        ]
        """
        partition = self.summary_partition(allele)
        if self.has_family_bins():
            partition.append((
                "family_bin",
                str(self.make_family_bin(allele.family_id))
            ))
        return partition

    def get_variant_partitions(self, chrom_lens: dict[str, int]) \
            -> tuple[list[list[tuple[str, str]]], list[list[tuple[str, str]]]]:
        """Return the output summary and family variant partition names."""
        summary_parts = []
        if self.has_region_bins():
            other_max_len = -1
            for chrom, chrom_len in chrom_lens.items():
                if chrom not in self.chromosomes:
                    other_max_len = max(other_max_len, chrom_len)
                    continue

                num_buckets = math.ceil(chrom_len / self.region_length)
                for bin_i in range(num_buckets):
                    summary_parts.append([("region_bin", f"{chrom}_{bin_i}")])

            if other_max_len > 0:
                num_buckets = math.ceil(other_max_len / self.region_length)
                for bin_i in range(num_buckets):
                    summary_parts.append([("region_bin", f"other_{bin_i}")])
        if self.has_frequency_bins():
            summary_parts = self._add_product(
                summary_parts, [("frequency_bin", str(i)) for i in range(4)]
            )
        if self.has_coding_bins():
            summary_parts = self._add_product(
                summary_parts, [("coding_bin", str(i)) for i in range(2)]
            )

        if self.has_family_bins():
            family_parts = self._add_product(
                summary_parts,
                [("family_bin", str(i)) for i in range(self.family_bin_size)]
            )
        else:
            family_parts = summary_parts

        return summary_parts, family_parts

    @staticmethod
    def _add_product(names, to_add):
        res = []
        for name in names:
            for name_to_add in to_add:
                res.append([*name, name_to_add])
        return res

    @staticmethod
    def partition_directory(
            output_dir: str, partition: List[Tuple[str, str]]) -> str:
        """Construct a partition dataset directory.

        Given a partition in the format returned by `summary_parition` or
        `family_partition` methods, this function constructs the directory name
        corresponding to the partition.
        """
        return fs_utils.join(
            output_dir, *[
                f"{bname}={bvalue}" for (bname, bvalue) in partition])

    @staticmethod
    def partition_filename(
            prefix: str, partition: List[Tuple[str, str]],
            bucket_index: int) -> str:
        """Construct a partition dataset base filename.

        Given a partition in the format returned by `summary_parition` or
        `family_partition` methods, this function constructs the file name
        corresponding to the partition.
        """
        partition_parts = [
            f"{bname}_{bvalue}" for (bname, bvalue) in partition]
        parts = [
            prefix, *partition_parts]
        if bucket_index is not None:
            parts.append(f"bucket_index_{bucket_index:0>6}")
        result = "_".join(parts)
        result += ".parquet"
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert the partition descriptor to a dict."""
        result: Dict[str, Any] = {}
        result["chromosomes"] = self.chromosomes
        result["region_length"] = self.region_length
        result["rare_boundary"] = self.rare_boundary
        result["coding_effect_types"] = self.coding_effect_types
        result["family_bin_size"] = self.family_bin_size
        return result

    def serialize(self, output_format: str = "conf") -> str:
        """Serialize a partition descriptor into a string."""
        if output_format == "conf":
            return jinja2.Template(textwrap.dedent("""
                {% if chromosomes %}
                [region_bin]
                chromosomes={{ chromosomes|join(', ') }}
                region_length={{ region_length }}
                {% endif %}
                {% if rare_boundary %}
                [frequency_bin]
                rare_boundary={{ rare_boundary }}
                {% endif %}
                {% if coding_effect_types %}
                [coding_bin]
                coding_effect_types={{ coding_effect_types|join(', ') }}
                {% endif %}
                {% if family_bin_size %}
                [family_bin]
                family_bin_size={{ family_bin_size }}
                {% endif %}
            """)).render(self.to_dict())
        if output_format == "yaml":
            return jinja2.Template(textwrap.dedent("""
                {% if chromosomes %}
                region_bin:
                  chromosomes: {{ chromosomes|join(', ') }}
                  region_length: {{ region_length }}
                {% endif %}
                {% if rare_boundary %}
                frequency_bin:
                  rare_boundary: {{ rare_boundary }}
                {% endif %}
                {% if coding_effect_types %}
                coding_bin:
                  coding_effect_types: {{ coding_effect_types|join(', ') }}
                {% endif %}
                {% if family_bin_size %}
                family_bin:
                  family_bin_size: {{ family_bin_size }}
                {% endif %}
            """)).render(self.to_dict())
        raise ValueError(
            f"usupported output format for partition descriptor: "
            f"<{output_format}>")
