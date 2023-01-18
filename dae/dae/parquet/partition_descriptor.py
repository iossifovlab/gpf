from __future__ import annotations

import hashlib
import pathlib
import configparser

from typing import Optional, List, Iterable, Set, Tuple, Union, Dict, Any

import yaml

from dae.variants.attributes import TransmissionType
from dae.utils import fs_utils


class PartitionDescriptor:
    """Class to represent partition of a genotype dataset."""

    def __init__(
            self,
            chromosomes: Optional[List[str]] = None,
            region_length: int = 0,
            family_bin_size: int = 0,
            coding_effect_types: Optional[List[str]] = None,
            rare_boundary: float = 0):

        self._chromosomes = chromosomes
        self._region_length = region_length
        self._family_bin_size = family_bin_size
        self._coding_effect_types: Set[str] = \
            set(coding_effect_types) if coding_effect_types else set()
        self._rare_boundary = rare_boundary

    family_alleles_dirname: str = "family"
    summary_alleles_dirname: str = "summary"

    @staticmethod
    def _configparser_parse(content: str):
        parser = configparser.ConfigParser()
        parser.read_string(content)
        return parser

    @staticmethod
    def parse(path_name: Union[pathlib.Path, str]) -> PartitionDescriptor:
        """Parse partition description from a file."""
        if isinstance(path_name, str):
            path_name = pathlib.Path(path_name)
        if path_name.suffix == ".conf":
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
            content: Optional[str],
            content_format: str = "conf") -> PartitionDescriptor:
        """Parse partition description from a string."""
        config = {
            "region_length": 0,
            "chromosomes": [],
            "family_bin_size": 0,
            "coding_effect_types": set(),
            "rare_boundary": 0.0
        }
        if not content:
            return PartitionDescriptor._from_dict(config)
        if content_format == "conf":
            parsed_data = PartitionDescriptor._configparser_parse(content)
        elif content_format == "yaml":
            parsed_data = yaml.safe_load(content)
        else:
            raise ValueError(
                f"unsuported partition description format <{content_format}>")

        if "region_bin" in parsed_data.keys():
            config["region_length"] = int(
                parsed_data["region_bin"]["region_length"])
            config["chromosomes"] = [
                c.strip()
                for c in parsed_data["region_bin"]["chromosomes"].split(",")]

        if "family_bin" in parsed_data.keys():
            config["family_bin_size"] = int(
                parsed_data["family_bin"]["family_bin_size"])

        if "frequency_bin" in parsed_data.keys():
            config["rare_boundary"] = float(
                parsed_data["frequency_bin"]["rare_boundary"])

        if "coding_bin" in parsed_data.keys():
            config["coding_effect_types"] = set(
                s.strip()
                for s in parsed_data["coding_bin"][
                    "coding_effect_types"
                ].split(",")
            )
        return PartitionDescriptor._from_dict(config)

    @staticmethod
    def _from_dict(config: Dict[str, Any]) -> PartitionDescriptor:
        return PartitionDescriptor(
            chromosomes=config.get("chromosomes"),
            region_length=config.get("region_length", 0),
            family_bin_size=config.get("family_bin_size", 0),
            rare_boundary=config.get("rare_boundary", 0.0),
            coding_effect_types=config.get("conding_effect_types")
        )

    def has_region_bins(self):
        return (self._chromosomes and self._region_length > 0)

    def has_family_bins(self):
        return self._family_bin_size > 0

    def has_coding_bins(self):
        return self._coding_effect_types

    def has_frequency_bins(self):
        return self._rare_boundary > 0

    def has_partitions(self):
        return self.has_region_bins() or self.has_frequency_bins() or \
            self.has_coding_bins() or self.has_family_bins()

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

    def serialize(self) -> str:
        return ""

    def make_region_bin(self, chrom: str, pos: int) -> str:
        """Produce region bin from chromosome and position."""
        if not self.has_region_bins():
            raise ValueError(
                f"Partition <{self.serialize()}> does not define region bins.")
        assert self._chromosomes is not None
        assert self._region_length > 0

        pos_bin = pos // self._region_length
        if chrom in self._chromosomes:
            return f"{chrom}_{pos_bin}"

        return f"other_{pos_bin}"

    def make_family_bin(self, family_id: str) -> int:
        """Produce family bin from family ID."""
        if not self.has_family_bins():
            raise ValueError(
                f"Partition <{self.serialize()}> does not define family bins.")
        sha256 = hashlib.sha256()
        sha256.update(family_id.encode())
        digest = int(sha256.hexdigest(), 16)
        return int(digest % self.family_bin_size)

    def make_coding_bin(self, effect_types: Iterable[str]) -> int:
        """Produce coding bin from list of effect types."""
        if not self.has_coding_bins():
            raise ValueError(
                f"Partition <{self.serialize()}> does not define coding bins.")
        variant_effects = set(effect_types)

        result = variant_effects.intersection(self._coding_effect_types)
        if len(result) == 0:
            return 0
        return 1

    def make_frequency_bin(
            self, allele_count: Optional[int], allele_freq: Optional[float],
            is_denovo: bool = False):
        """Produce frequency bin.

        Params are allele count, allele frequence and de Novo flag.
        """
        if is_denovo:
            frequency_bin = 0
        elif allele_count and int(allele_count) == 1:  # Ultra rare
            frequency_bin = 1
        elif allele_freq and float(allele_freq) < self._rare_boundary:  # Rare
            frequency_bin = 2
        else:  # Common
            frequency_bin = 3

        return frequency_bin

    def summary_partition(self, allele) -> List[Tuple[str, str]]:
        """Produce summary partition for an allele."""
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

    @staticmethod
    def partition_directory(
            output_dir: str, partition: List[Tuple[str, str]]) -> str:
        """Construct a partition dataset directory."""
        return fs_utils.join(
            output_dir, *[
                f"{bname}={bvalue}" for (bname, bvalue) in partition])

    @staticmethod
    def partition_filename(
            prefix: str, partition: List[Tuple[str, str]],
            bucket_index: int) -> str:
        """Construct a partition dataset base filename."""
        partition_parts = [
            f"{bname}_{bvalue}" for (bname, bvalue) in partition]
        parts = [
            prefix, *partition_parts, f"bucket_index_{bucket_index:0>6}"]
        result = "_".join(parts)
        result += ".parquet"
        return result

    def summary_filename(self, summary_allele):
        raise NotImplementedError()

    def family_filename(self, family_allele):
        raise NotImplementedError()

    def write_partition_configuration(self):
        raise NotImplementedError()
