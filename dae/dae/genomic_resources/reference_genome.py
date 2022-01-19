# June 6th 2013
# by Ewa

import os
import logging

from typing import List, Tuple

from dae.utils.regions import Region


logger = logging.getLogger(__name__)


class ReferenceGenome:

    def __init__(self, source: Tuple[str, ...]):
        self._index = None
        self._chromosomes = None
        self._sequence = None
        self.PARS = {}
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
