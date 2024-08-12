from __future__ import annotations

import configparser
import hashlib
import math
import pathlib
import sys
import textwrap
from collections import defaultdict
from collections.abc import Iterable
from math import ceil
from typing import Any, cast

import jinja2
import toml
import yaml

from dae.effect_annotation.effect import expand_effect_types
from dae.utils import fs_utils
from dae.utils.regions import Region
from dae.variants.attributes import TransmissionType
from dae.variants.family_variant import FamilyAllele
from dae.variants.variant import SummaryAllele


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
        pos_bin = pos // self.region_length

        if chrom in self.chromosomes:
            return f"{chrom}_{pos_bin}"

        return f"other_{pos_bin}"

    def region_to_bins(
        self, region: Region, chrom_lens: dict[str, int],
    ) -> list[tuple[str, str]]:
        """Provide a list of bins the given region intersects."""
        start = region.start or 0
        stop = min(region.stop or start, chrom_lens[region.chrom] - 1)
        if start == stop:
            return [("region_bin", self.make_region_bin(region.chrom, start))]
        return [
            ("region_bin", self.make_region_bin(region.chrom,
                                                i * self.region_length))
            for i in range(int(start / self.region_length),
                           int(stop / self.region_length) + 1)
        ]

    def _make_region_bins(
        self, chrom: str,
        start: int,
        end: int,
    ) -> list[str]:
        return [
            f"{chrom}_{i}"

            for i in range(
                int(start / self.region_length),
                int(end / self.region_length) + 1)
        ]

    def make_all_region_bins(self, chrom_lens: dict[str, int])  -> list[str]:
        """Produce all region bins for all chromosomes."""
        bins = []

        for chrom in self.chromosomes:
            if chrom not in chrom_lens:
                raise ValueError(
                    f"Partition descriptor chromosome <{chrom}> "
                    f"not found in reference genome chromosome lengths.")

            chrom_len = chrom_lens[chrom]
            bins.extend(
                self._make_region_bins(chrom, 0, chrom_len),
            )
        other_chroms = set(chrom_lens.keys()) - set(self.chromosomes)
        if other_chroms:
            max_other_len = max(
                chrom_lens[chrom] for chrom in other_chroms)
            bins.extend(
                self._make_region_bins("other", 1, max_other_len),
            )
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

    def dataset_summary_partition(self) -> list[tuple[str, str]]:
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

    def dataset_family_partition(self) -> list[tuple[str, str]]:
        """Build family dataset partition for table creation.

        When creating an Impala or BigQuery table it is helpful to have
        the list of partitions and types used in the parquet dataset.
        """
        result = self.dataset_summary_partition()
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
                summary_parts.extend([
                    [("region_bin", f"{chrom}_{bin_i}")]
                    for bin_i in range(num_buckets)
                ])

            if other_max_len > 0:
                num_buckets = math.ceil(other_max_len / self.region_length)
                summary_parts.extend([
                    [("region_bin", f"other_{bin_i}")]
                    for bin_i in range(num_buckets)
                ])
        if self.has_frequency_bins():
            summary_parts = self._add_product(
                summary_parts, [("frequency_bin", str(i)) for i in range(4)],
            )
        if self.has_coding_bins():
            summary_parts = self._add_product(
                summary_parts, [("coding_bin", str(i)) for i in range(2)],
            )

        if self.has_family_bins():
            family_parts = self._add_product(
                summary_parts,
                [("family_bin", str(i)) for i in range(self.family_bin_size)],
            )
        else:
            family_parts = summary_parts

        return summary_parts, family_parts

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
            output_dir: str, partition: list[tuple[str, str]]) -> str:
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
            prefix: str, partition: list[tuple[str, str]],
            bucket_index: int | None) -> str:
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
            target = chrom
            if chrom not in self.chromosomes:
                target = "other"
            region_bins_count = self.region_bins_count(
                chrom, chromosome_lengths)

            if region_bins_count == 1:
                region_bin = f"{target}_0"
                result[region_bin].append(Region(chrom))
                continue

            for region_index in range(region_bins_count):
                start = region_index * self.region_length + 1
                end = (region_index + 1) * self.region_length
                end = min(end, chromosome_lengths[chrom])
                region_bin = f"{target}_{region_index}"
                result[region_bin].append(Region(chrom, start, end))
        return result
