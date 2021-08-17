import os
import logging

from copy import deepcopy

from dae.genomic_resources.resources import GenomicResource
from dae.configuration.schemas.genomic_score_database import \
    genomic_sequence_schema

logger = logging.getLogger(__name__)


class GenomicSequenceResource(GenomicResource):

    def open(self):
        genomic_file = f"{self._url}/{self._config.filename}"
        genomic_index_file = f"{self._url}/{self._config.index_file.filename}"

        print(genomic_file, genomic_index_file)

    @classmethod
    def get_config_schema(cls):
        schema = deepcopy(genomic_sequence_schema)
        return schema

    # def __init__(self):
    #     self.genomic_file = None
    #     self.genomic_index_file = None
    #     self.chromosomes = None
    #     self._indexing = {}

    def __create_index_file(self, file):
        from pysam import faidx

        faidx(file)

    def __chrom_names(self):
        with open(self.genomic_index_file) as infile:
            chroms = []

            while True:
                line = infile.readline()
                if not line:
                    break
                line = line.split()
                chroms.append(line[0])

        self.chromosomes = chroms

    def __initiate(self):
        self._indexing = {}
        with open(self.genomic_index_file, "r") as infile:
            while True:
                line = infile.readline()
                if not line:
                    break
                line = line.split()
                self._indexing[line[0]] = {
                    "length": int(line[1]),
                    "startBit": int(line[2]),
                    "seqLineLength": int(line[3]),
                    "lineLength": int(line[4]),
                }

        self.__f = open(self.genomic_file, "r")

    def close(self):
        self.__f.close()

    # @staticmethod
    # def load_genome(filename):
    #     genome = GenomicSequence()
    #     genome._load_genome(filename)
    #     return genome

    def _load_genome(self, filename):
        assert os.path.exists(filename), filename
        assert filename.endswith(".fa")

        self.genomic_index_file = f"{filename}.fai"
        self.genomic_file = filename

        if not os.path.exists(self.genomic_index_file):
            self.__create_index_file(filename)

        self.__chrom_names()
        self.__initiate()

        return self

    def get_chrom_length(self, chrom):

        try:
            return self._indexing[chrom]["length"]
        except KeyError:
            logger.warning(f"unknown chromosome: {chrom}")
            return None

    def get_all_chrom_lengths(self):
        result = []
        for chrom in self.chromosomes:
            result.append((chrom, self._indexing[chrom]["length"]))
        return result

    def get_sequence(self, chrom, start, stop):
        if chrom not in self.chromosomes:
            logger.warning(f"unknown chromosome: {chrom}")
            return None

        self.__f.seek(
            self._indexing[chrom]["startBit"]
            + start
            - 1
            + (start - 1) / self._indexing[chrom]["seqLineLength"]
        )

        ll = stop - start + 1
        x = 1 + ll // self._indexing[chrom]["seqLineLength"]

        w = self.__f.read(ll + x)
        w = w.replace("\n", "")[:ll]

        return w.upper()