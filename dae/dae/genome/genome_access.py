# June 6th 2013
# by Ewa

import os
import copy
import abc
import logging

from typing import List

from dae.utils.regions import Region


logger = logging.getLogger(__name__)


class GenomicSequenceBase:

    def __init__(self):
        self._index = None
        self._chromosomes = None
        self._sequence = None
        self.PARS = {}

    @property
    def chromosomes(self):
        return self._chromosomes

    @abc.abstractmethod
    def open(self):
        pass

    def _load_genome_index(self, index_content):
        self._index = {}
        for line in index_content.split("\n"):
            line = line.strip()
            print(line)
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

        w = self._sequence.read(ll + x)
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


class GenomicSequence(GenomicSequenceBase):

    def __init__(self, genome_filename, PARS=None):
        super(GenomicSequence, self).__init__()
        assert os.path.exists(genome_filename)

        self.genome_filename = genome_filename
        if PARS is not None:
            self.PARS = copy.deepcopy(PARS)

    def open(self):
        index_filename = f"{self.genome_filename}.fai"
        assert os.path.exists(index_filename)
        with open(index_filename) as index_file:
            content = index_file.read()
            self._load_genome_index(content)

        self._sequence = open(self.genome_filename)

    def create_index_file(self):
        from pysam import faidx
        faidx(self.genome_filename)

    @staticmethod
    def load_genome(filename):
        genome = GenomicSequence(filename)
        genome.open()
        return genome


def open_ref(filename):
    return GenomicSequence.load_genome(filename)
