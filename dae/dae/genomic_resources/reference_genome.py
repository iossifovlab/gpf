"""Defines reference genome class."""

import os
import logging

from typing import List, Tuple, Optional, Dict, Any, cast

from dae.utils.regions import Region
from dae.genomic_resources import GenomicResource


logger = logging.getLogger(__name__)


class ReferenceGenome:
    """Provides an interface for quering a reference genome."""

    def __init__(self, source: Tuple[str, ...]):
        self._index: Dict[str, Any] = {}
        self._chromosomes: List[str] = []
        self._sequence = None
        self.pars: dict = {}
        self.source = source

    @property
    def chromosomes(self) -> List[str]:
        """Return a list of all chromosomes of the reference genome."""
        return self._chromosomes

    def _load_genome_index(self, index_content):
        for line in index_content.split("\n"):
            line = line.strip()
            if not line:
                break
            line = line.split()

            self._index[line[0]] = {
                "length": int(line[1]),
                "startBit": int(line[2]),
                "seqLineLength": int(line[3]),
                "lineLength": int(line[4]),
            }
        self._chromosomes = list(self._index.keys())

    def set_open(self, index_content, sequence_file):
        """Set up working reference genome instance."""
        self._sequence = sequence_file
        self._load_genome_index(index_content)

    def set_pars(self, pars):
        """Set up PARS definition in the reference genome."""
        self.pars = pars

    def close(self):
        """Close reference genome sequence file-like objects."""
        self._sequence.close()

    def get_chrom_length(self, chrom: str) -> int:
        """Return the length of a specified chromosome."""
        chrom_data = self._index.get(chrom)
        if chrom_data is None:
            raise ValueError(f"can't fined chromosome {chrom}")
        return cast(int, chrom_data["length"])

    def get_all_chrom_lengths(self):
        """Return list of all chromosomes lengths."""
        return [
            (key, value["length"])
            for key, value in self._index.items()]

    def get_sequence(self, chrom, start, stop):
        """Return sequence of nucleotides from specified chromosome region."""
        if chrom not in self.chromosomes:
            logger.warning(
                "chromosome %s not found in %s", chrom, self.source)
            return None

        self._sequence.seek(
            self._index[chrom]["startBit"]
            + start
            - 1
            + (start - 1) // self._index[chrom]["seqLineLength"]
        )

        length = stop - start + 1
        line_feeds = 1 + length // self._index[chrom]["seqLineLength"]

        sequence = self._sequence.read(length + line_feeds).decode("ascii")
        sequence = sequence.replace("\n", "")[:length]
        return sequence.upper()

    def is_pseudoautosomal(self, chrom: str, pos: int) -> bool:
        """Return true if specified position is pseudoautosomal."""
        def in_any_region(
                chrom: str, pos: int, regions: List[Region]) -> bool:
            return any(map(lambda reg: reg.isin(chrom, pos), regions))

        pars_regions = self.pars.get(chrom, None)
        if pars_regions:
            return in_any_region(
                chrom, pos, pars_regions  # type: ignore
            )
        return False


def open_reference_genome_from_file(filename) -> ReferenceGenome:
    """Open a reference genome from a file."""
    ref = ReferenceGenome(("file", filename))
    index_filename = f"{filename}.fai"
    assert os.path.exists(index_filename)
    with open(index_filename, encoding="utf8") as index_file:
        content = index_file.read()
    ref.set_open(content, open(filename, "rb"))
    return ref


def _parse_pars(config) -> Optional[dict]:
    if "PARS" not in config:
        return None

    assert config["PARS"]["X"] is not None
    regions_x = [
        Region.from_str(region) for region in config["PARS"]["X"]
    ]
    chrom_x = regions_x[0].chrom

    result = {
        chrom_x: regions_x
    }

    if config["PARS"]["Y"] is not None:
        regions_y = [
            Region.from_str(region) for region in config["PARS"]["Y"]
        ]
        chrom_y = regions_y[0].chrom
        result[chrom_y] = regions_y
    return result


def open_reference_genome_from_resource(
        resource: Optional[GenomicResource]) -> ReferenceGenome:
    """Open a reference genome from resource."""
    if resource is None:
        raise ValueError("None resource passed")

    if resource.get_type() != "genome":
        logger.error(
            "trying to open a resource %s of type "
            "%s as reference genome",
            resource.resource_id, resource.get_type())
        raise ValueError(f"wrong resource type: {resource.resource_id}")

    config = resource.get_config()
    file_name = config["filename"]
    index_file_name = config.get("index_file", f"{file_name}.fai")

    index_content = resource.get_file_content(index_file_name)

    ref = ReferenceGenome(
        ("resource", resource.proto.get_id(), resource.resource_id))

    pars = _parse_pars(config)
    ref.set_pars(pars)

    ref.set_open(
        index_content,
        resource.open_raw_file(
            file_name, "rb", uncompress=False, seekable=True))
    return ref
