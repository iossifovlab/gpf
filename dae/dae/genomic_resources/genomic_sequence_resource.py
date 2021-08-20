import logging

from copy import deepcopy

from dae.genomic_resources.resources import GenomicResource
from dae.configuration.schemas.genomic_score_database import \
    genomic_sequence_schema

logger = logging.getLogger(__name__)


class GenomicSequenceResource(GenomicResource):

    def __init__(self, config, repo):
        super().__init__(config, repo)
        self._index = None
        self._chromosomes = None
        self._sequence = None

    @property
    def chromosomes(self):
        return self._chromosomes

    def open(self):
        genomic_file = f"{self.get_url()}/" \
            f"{self.get_config().filename}"
        genomic_index_file = f"{self.get_url()}/" \
            f"{self.get_config().index_file.filename}"

        print(genomic_file, genomic_index_file)

        index_filename = self.get_config().index_file.filename
        with self.open_file(index_filename) as index_file:
            content = index_file.read()
            print(content)
            self._load_genome_index(content)
        self._sequence = self.open_file(self.get_config().filename)

    @classmethod
    def get_config_schema(cls):
        schema = deepcopy(genomic_sequence_schema)
        return schema

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
