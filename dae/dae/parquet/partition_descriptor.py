from __future__ import annotations

import configparser
import hashlib
import pathlib
import sys
import textwrap
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from math import ceil
from typing import Any, cast

import jinja2
import toml
import yaml

from dae.effect_annotation.effect import expand_effect_types
from dae.utils import fs_utils
from dae.utils.regions import (
    Region,
    calc_bin_begin,
    calc_bin_end,
    calc_bin_index,
)
from dae.variants.attributes import TransmissionType
from dae.variants.family_variant import FamilyAllele
from dae.variants.variant import SummaryAllele


@dataclass(frozen=True, eq=True)
class Partition:
    """Class to represent a partition of a genotype dataset."""
    region_bin: str | None = None
    frequency_bin: str | None = None
    coding_bin: str | None = None
    family_bin: str | None = None

    def to_pylist(self) -> list[tuple[str, str]]:
        """Convert the partition to a list of tuples."""
        result = []
        if self.region_bin is not None:
            result.append(("region_bin", self.region_bin))
        if self.frequency_bin is not None:
            result.append(("frequency_bin", self.frequency_bin))
        if self.coding_bin is not None:
            result.append(("coding_bin", self.coding_bin))
        if self.family_bin is not None:
            result.append(("family_bin", self.family_bin))
        return result

    @staticmethod
    def from_pylist(
        partition: list[tuple[str, str]],
    ) -> Partition:
        """Create a partition from a list of tuples."""
        region_bin = None
        frequency_bin = None
        coding_bin = None
        family_bin = None
        for name, value in partition:
            if name == "region_bin":
                region_bin = value
            elif name == "frequency_bin":
                frequency_bin = value
            elif name == "coding_bin":
                coding_bin = value
            elif name == "family_bin":
                family_bin = value
        return Partition(
            region_bin=region_bin,
            frequency_bin=frequency_bin,
            coding_bin=coding_bin,
            family_bin=family_bin,
        )

    def is_empty(self) -> bool:
        """Check if the partition is empty."""
        return (self.region_bin is None and
                self.frequency_bin is None and
                self.coding_bin is None and
                self.family_bin is None)

    def __repr__(self) -> str:
        """Return a string representation of the partition."""
        partition_parts = [
            f"{bin_name}_{bin_value}"
            for (bin_name, bin_value) in self.to_pylist()]
        if not partition_parts:
            return "partition_empty"
        return f"partition_{'_'.join(partition_parts)}"


class PartitionDescriptor:
    """Class to represent partition of a genotype dataset."""

    # pylint: disable=too-many-public-methods
    def __init__(
            self, *,
            chromosomes: list[str] | None = None,
            region_length: int = 0,
            integer_region_bins: bool = False,
            family_bin_size: int = 0,
            coding_effect_types: list[str] | None = None,
            rare_boundary: float = 0):
        if chromosomes is None:
            self.chromosomes: list[str] = []
        else:
            self.chromosomes = chromosomes
        self.region_length = region_length
        self.integer_region_bins = integer_region_bins
        self.family_bin_size = family_bin_size
        self.coding_effect_types: set[str] = \
            set(coding_effect_types) if coding_effect_types else set()
        self.rare_boundary = rare_boundary

    @staticmethod
    def parse(path_name: pathlib.Path | str) -> PartitionDescriptor:
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
            return PartitionDescriptor.parse_string(
                pathlib.Path(path_name).read_text(encoding="utf8"), "conf")
        if path_name.suffix == ".yaml":
            # parse YAML content
            return PartitionDescriptor.parse_string(
                pathlib.Path(path_name).read_text(encoding="utf8"), "yaml")

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
        integer_region_bins = False
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
            integer_region_bins: False
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
            try:
                parsed_data = toml.loads(content)
            except toml.TomlDecodeError:
                parser = configparser.ConfigParser()
                parser.read_string(content)
                parsed_data = cast(dict[str, Any], parser)

        elif content_format == "yaml":
            parsed_data = yaml.safe_load(content)
        else:
            raise ValueError(
                f"unsuported partition description format <{content_format}>")

        return PartitionDescriptor.parse_dict(parsed_data)

    @staticmethod
    def parse_dict(config_dict: dict[str, Any]) -> PartitionDescriptor:
        """Parse configuration dictionary and create a partion descriptor."""
        config: dict[str, Any] = {}
        if "region_bin" in config_dict:
            config["region_length"] = int(
                config_dict["region_bin"].get("region_length", sys.maxsize))
            config["integer_region_bins"] = bool(
                config_dict["region_bin"].get("integer_region_bins", False))
            chromosomes = config_dict["region_bin"]["chromosomes"]

            if isinstance(chromosomes, int):
                config["chromosomes"] = [str(chromosomes)]
            elif isinstance(chromosomes, str):
                config["chromosomes"] = [
                    c.strip()
                    for c in chromosomes.split(",")]
            elif isinstance(chromosomes, list):
                config["chromosomes"] = chromosomes
            else:
                raise ValueError(
                    f"unexpected chromosomes types: {type(chromosomes)} "
                    f"{chromosomes}")

        if "family_bin" in config_dict:
            config["family_bin_size"] = int(
                config_dict["family_bin"]["family_bin_size"])

        if "frequency_bin" in config_dict:
            config["rare_boundary"] = float(
                config_dict["frequency_bin"]["rare_boundary"])

        if "coding_bin" in config_dict:
            coding_effect_types = \
                config_dict["coding_bin"]["coding_effect_types"]
            if isinstance(coding_effect_types, str):
                result = {
                    s.strip()
                    for s in coding_effect_types.split(",")
                }
            else:
                assert isinstance(coding_effect_types, list)
                result = set(coding_effect_types)
            config["coding_effect_types"] = set(expand_effect_types(result))

        return PartitionDescriptor(
            chromosomes=config.get("chromosomes"),
            region_length=config.get("region_length", 0),
            integer_region_bins=config.get("integer_region_bins", False),
            family_bin_size=config.get("family_bin_size", 0),
            rare_boundary=config.get("rare_boundary", 0.0),
            coding_effect_types=config.get("coding_effect_types"),
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
        assert pos > 0
        pos_bin = calc_bin_index(self.region_length, pos)

        if chrom in self.chromosomes:
            if self.integer_region_bins:
                chrom_index = self.chromosomes.index(chrom)
                return f"{chrom_index * 10_000 + pos_bin}"

            return f"{chrom}_{pos_bin}"

        if self.integer_region_bins:
            return f"{10_000_000 + pos_bin}"
        return f"other_{pos_bin}"

    def region_bins_count(
        self, chrom: str,
        chromosome_lengths: dict[str, int],
    ) -> int:
        return ceil(
            chromosome_lengths[chrom]
            / self.region_length,
        )

    def make_region_bins_regions(
            self, chromosomes: list[str],
            chromosome_lengths: dict[str, int],
    ) -> dict[str, list[Region]]:
        """Generate region_bin to regions based on a partition descriptor."""
        assert self.has_region_bins()

        result = defaultdict(list)
        for chrom in chromosomes:
            region_bins_count = self.region_bins_count(
                chrom, chromosome_lengths)

            if region_bins_count == 1:
                region_bin = self.make_region_bin(chrom, 1)
                result[region_bin].append(Region(chrom))
                continue

            for region_index in range(region_bins_count):
                start = calc_bin_begin(self.region_length, region_index)
                end = calc_bin_end(self.region_length, region_index)
                end = min(end, chromosome_lengths[chrom])
                region_bin = self.make_region_bin(chrom, start)
                result[region_bin].append(Region(chrom, start, end))
        return result

    def region_to_region_bins(
        self, region: Region, chrom_lens: dict[str, int],
    ) -> list[str]:
        """Provide a list of bins the given region intersects."""
        start = region.start or 1
        stop = region.stop or chrom_lens[region.chrom]
        stop = min(stop or start, chrom_lens[region.chrom])

        assert start > 0
        assert stop > 0

        if start == stop:
            return [self.make_region_bin(region.chrom, start)]
        return [
            self.make_region_bin(
                region.chrom, calc_bin_begin(self.region_length, i))
            for i in range(calc_bin_index(self.region_length, start),
                           calc_bin_index(self.region_length, stop) + 1)
        ]

    def make_all_region_bins(
        self, chromosome_lengths: dict[str, int],
    ) -> list[str]:
        """Produce all region bins for all chromosomes."""
        bins = []

        genome_chroms = set(chromosome_lengths.keys())
        partition_chroms = set(self.chromosomes) & genome_chroms

        for chrom in partition_chroms:
            if chrom not in chromosome_lengths:
                raise ValueError(
                    f"Partition descriptor chromosome <{chrom}> "
                    f"not found in reference genome chromosome lengths. "
                    f"Chromosomes: {chromosome_lengths.keys()}")

            chrom_len = chromosome_lengths[chrom]
            bins.extend(
                self.region_to_region_bins(
                    Region(chrom, 1, chrom_len),
                    chromosome_lengths,
                ))
        other_chroms = genome_chroms - partition_chroms
        if other_chroms:
            max_other_len = 0
            max_chrom = ""
            for chrom in other_chroms:
                if chromosome_lengths[chrom] > max_other_len:
                    max_other_len = chromosome_lengths[chrom]
                    max_chrom = chrom

            bins.extend(
                self.region_to_region_bins(
                    Region(max_chrom, 1, max_other_len),
                    chromosome_lengths,
                ))
        return bins

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
            self, allele_count: int, allele_freq: float, *,
            is_denovo: bool = False) -> str:
        """Produce frequency bin from allele count, frequency and de Novo flag.

        Params are allele count, allele frequence and de Novo flag.
        """
        if is_denovo:
            return "0"
        if int(allele_count) <= 1:  # Ultra rare
            return "1"
        if allele_freq <= self.rare_boundary:  # Rare
            return "2"

        return "3"

    def summary_partition_schema(self) -> list[tuple[str, str]]:
        """Build summary parquet dataset partition schema for table creation.

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

    def family_partition_schema(self) -> list[tuple[str, str]]:
        """Build family dataset partition schema for table creation.

        When creating an Impala or BigQuery table it is helpful to have
        the list of partitions and types used in the parquet dataset.
        """
        result = self.summary_partition_schema()
        if self.has_family_bins():
            result.append(("family_bin", "int8"))
        return result

    def summary_partition(
        self, allele: SummaryAllele, *,
        seen_as_denovo: bool,
    ) -> list[tuple[str, str]]:
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
            allele_count = allele.get_attribute("af_allele_count", 0)
            allele_freq = allele.get_attribute("af_allele_freq", 0)
            result.append((
                "frequency_bin",
                str(self.make_frequency_bin(
                    allele_count=allele_count,
                    allele_freq=allele_freq,
                    is_denovo=seen_as_denovo)),
            ))
        if self.has_coding_bins():
            coding_bin = 0
            if allele.is_reference_allele:
                coding_bin = 0
            else:
                coding_bin = self.make_coding_bin(allele.effect_types)
            result.append(("coding_bin", str(coding_bin)))

        return result

    def family_partition(
        self, allele: FamilyAllele, *,
        seen_as_denovo: bool,
    ) -> list[tuple[str, str]]:
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
        partition = self.summary_partition(
            allele, seen_as_denovo=seen_as_denovo)
        if self.has_family_bins():
            partition.append((
                "family_bin",
                str(self.make_family_bin(allele.family_id)),
            ))
        return partition

    def schema1_partition(
        self, allele: FamilyAllele,
    ) -> list[tuple[str, str]]:
        """Produce Schema1 family partition for an allele.

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
        is_denovo = allele.transmission_type == TransmissionType.denovo
        partition = self.summary_partition(allele, seen_as_denovo=is_denovo)
        if self.has_family_bins():
            partition.append((
                "family_bin",
                str(self.make_family_bin(allele.family_id)),
            ))
        return partition

    def get_variant_partitions(
        self, chromosome_lengths: dict[str, int],
    ) -> tuple[list[list[tuple[str, str]]], list[list[tuple[str, str]]]]:
        """Return the output summary and family variant partition names."""
        summary_parts = self._build_summary_partitions(chromosome_lengths)
        family_parts = self._build_family_partitions(chromosome_lengths)
        return summary_parts, family_parts

    def _build_summary_partitions(
        self, chromosome_lengths: dict[str, int],
    ) -> list[list[tuple[str, str]]]:
        """Build summary partitions for all variants in the dataset."""
        summary_parts: list[list[tuple[str, str]]] = []
        if self.has_region_bins():
            summary_parts.extend(
                [("region_bin", r)]
                for r in self.make_all_region_bins(chromosome_lengths)
            )
        if self.has_frequency_bins():
            summary_parts = self._add_product(
                summary_parts, [("frequency_bin", str(i)) for i in range(4)],
            )
        if self.has_coding_bins():
            summary_parts = self._add_product(
                summary_parts, [("coding_bin", str(i)) for i in range(2)],
            )
        return summary_parts

    def build_summary_partitions(
        self, chromosome_lengths: dict[str, int],
    ) -> list[Partition]:
        """Build summary partitions for all variants in the dataset."""
        summary_paritions = self._build_summary_partitions(chromosome_lengths)
        if not summary_paritions:
            return [Partition()]
        return [
            Partition.from_pylist(partition)
            for partition in summary_paritions
        ]

    def _build_family_partitions(
        self, chromosome_lengths: dict[str, int],
    ) -> list[list[tuple[str, str]]]:
        """Build family partitions for all variants in the dataset."""
        family_parts = self._build_summary_partitions(chromosome_lengths)
        if self.has_family_bins():
            family_parts = self._add_product(
                family_parts,
                [("family_bin", str(i)) for i in range(self.family_bin_size)],
            )
        return family_parts

    def build_family_partitions(
        self, chromosome_lengths: dict[str, int],
    ) -> list[Partition]:
        """Build summary partitions for all variants in the dataset."""
        family_partitions = self._build_family_partitions(chromosome_lengths)
        if not family_partitions:
            return [Partition()]
        return [
            Partition.from_pylist(partition)
            for partition in family_partitions
        ]

    @staticmethod
    def _add_product(
            names: list[list[tuple[str, str]]],
            to_add: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
        if len(names) == 0:
            return [[name] for name in to_add]

        return [
            [*name, name_to_add]
            for name in names
            for name_to_add in to_add
        ]

    @staticmethod
    def partition_directory(
        dataset_dir: str,
        partition: Partition | list[tuple[str, str]],
    ) -> str:
        """Construct a partition dataset directory.

        Given a partition in the format returned by `summary_parition` or
        `family_partition` methods, this function constructs the directory name
        corresponding to the partition.
        """
        if isinstance(partition, Partition):
            partition = partition.to_pylist()
        return fs_utils.join(
            dataset_dir, *[
                f"{bname}={bvalue}" for (bname, bvalue) in partition])

    @staticmethod
    def partition_filename(
        prefix: str, partition: Partition | list[tuple[str, str]],
        bucket_index: int | None,
    ) -> str:
        """Construct a partition dataset base filename.

        Given a partition in the format returned by `summary_parition` or
        `family_partition` methods, this function constructs the file name
        corresponding to the partition.
        """
        if isinstance(partition, Partition):
            partition = partition.to_pylist()
        partition_parts = [
            f"{bin_name}_{bin_value}" for (bin_name, bin_value) in partition]
        parts = [
            prefix, *partition_parts]
        if bucket_index is not None:
            parts.append(f"bucket_index_{bucket_index:0>6}")
        result = "_".join(parts)
        result += ".parquet"
        return result

    @staticmethod
    def path_to_partitions(raw_path: str) -> list[tuple[str, str]]:
        """Convert a path into the partitions it is composed of."""
        path = pathlib.Path(raw_path)
        parts = list(path.parts)
        if parts[-1].endswith(".parquet"):
            parts.pop(-1)

        if not all("=" in part for part in parts):
            raise ValueError("Path contains non-partition directories!")

        result = []
        for part in parts:
            partition = part.split("=", maxsplit=2)
            result.append((partition[0], partition[1]))
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert the partition descriptor to a dict."""
        result: dict[str, Any] = {}
        result["chromosomes"] = self.chromosomes
        result["region_length"] = self.region_length
        result["integer_region_bins"] = self.integer_region_bins
        result["rare_boundary"] = self.rare_boundary
        result["coding_effect_types"] = self.coding_effect_types
        result["family_bin_size"] = self.family_bin_size
        return result

    def serialize(self, output_format: str = "conf") -> str:
        """Serialize a partition descriptor into a string."""
        if output_format == "conf":
            return jinja2.Template(textwrap.dedent("""
                {%- if chromosomes %}
                [region_bin]
                chromosomes={{ chromosomes|join(',') }}
                region_length={{ region_length }}
                {%- if integer_region_bins %}
                integer_region_bins=true
                {%- endif %}
                {%- endif %}
                {%- if rare_boundary %}
                [frequency_bin]
                rare_boundary={{ rare_boundary }}
                {%- endif %}
                {%- if coding_effect_types %}
                [coding_bin]
                coding_effect_types={{ coding_effect_types|join(',') }}
                {%- endif %}
                {%- if family_bin_size %}
                [family_bin]
                family_bin_size={{ family_bin_size }}
                {%- endif %}
            """)).render(self.to_dict())
        if output_format == "yaml":
            return jinja2.Template(textwrap.dedent("""
                {%- if chromosomes %}
                region_bin:
                  chromosomes: {{ chromosomes|join(',') }}
                  region_length: {{ region_length }}
                {%- if integer_region_bins %}
                  integer_region_bins: true
                {%- endif %}
                {%- endif %}
                {%- if rare_boundary %}
                frequency_bin:
                  rare_boundary: {{ rare_boundary }}
                {%- endif %}
                {%- if coding_effect_types %}
                coding_bin:
                  coding_effect_types: {{ coding_effect_types|join(',') }}
                {%- endif %}
                {%- if family_bin_size %}
                family_bin:
                  family_bin_size: {{ family_bin_size }}
                {%- endif %}
            """)).render(self.to_dict())
        raise ValueError(
            f"usupported output format for partition descriptor: "
            f"<{output_format}>")
