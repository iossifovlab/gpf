import os
import logging

from typing import List, Tuple, Optional

from dae.utils.regions import Region
from dae.genomic_resources import GenomicResource


logger = logging.getLogger(__name__)


class ReferenceGenome:

    def __init__(self, source: Tuple[str, ...]):
        self._index = None
        self._chromosomes = None
        self._sequence = None
        self.PARS: dict = {}
        self.source = source

    @property
    def chromosomes(self):
        return self._chromosomes

    def _load_genome_index(self, index_content):
        self._index = {}
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
        self._sequence = sequence_file
        self._load_genome_index(index_content)

    def set_pars(self, PARS):
        self.PARS = PARS

    def close(self):
        self._sequence.close()

    def get_chrom_length(self, chrom):
        chrom_data = self._index.get(chrom)
        if chrom_data is None:
            return None
        return chrom_data["length"]

    def get_all_chrom_lengths(self):
        return [
            (key, value["length"])
            for key, value in self._index.items()]

    def get_sequence(self, chrom, start, stop):
        if chrom not in self.chromosomes:
            logger.warning(f"chromosome {chrom} not found in {self.get_id()}")
            return None

        self._sequence.seek(
            self._index[chrom]["startBit"]
            + start
            - 1
            + (start - 1) // self._index[chrom]["seqLineLength"]
        )

        ll = stop - start + 1
        x = 1 + ll // self._index[chrom]["seqLineLength"]

        w = self._sequence.read(ll + x).decode('ascii')
        w = w.replace("\n", "")[:ll]
        return w.upper()

    def is_pseudoautosomal(self, chrom: str, pos: int) -> bool:

        # TODO Handle variants which are both inside and outside a PARs
        # Currently, if the position of the reference is within a PAR,
        # the whole variant is considered to be within an autosomal region
        def in_any_region(
                chrom: str, pos: int, regions: List[Region]) -> bool:
            return any(map(lambda reg: reg.isin(chrom, pos), regions))

        pars_regions = self.PARS.get(chrom, None)
        if pars_regions:
            return in_any_region(
                chrom, pos, pars_regions  # type: ignore
            )
        else:
            return False


def open_reference_genome_from_file(filename) -> ReferenceGenome:
    ref = ReferenceGenome(('file', filename))
    index_filename = f"{filename}.fai"
    assert os.path.exists(index_filename)
    with open(index_filename) as index_file:
        content = index_file.read()
    ref.set_open(content, open(filename, 'rb'))
    return ref


def _parse_PARS(config) -> Optional[dict]:
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

    if resource is None:
        raise ValueError("None resource passed")

    if resource.get_type() != "genome":
        logger.error(
            f"trying to open a resource {resource.resource_id} of type "
            f"{resource.get_type()} as reference genome")
        raise ValueError(f"wrong resource type: {resource.resource_id}")

    config = resource.get_config()
    file_name = config["filename"]
    index_file_name = config.get("index_file", f"{file_name}.fai")

    index_content = resource.get_file_content(index_file_name)

    ref = ReferenceGenome(
        ('resource', resource.repo.repo_id, resource.resource_id))

    pars = _parse_PARS(config)
    ref.set_pars(pars)

    ref.set_open(
        index_content,
        resource.open_raw_file(
            file_name, "rb", uncompress=False, seekable=True))
    return ref
