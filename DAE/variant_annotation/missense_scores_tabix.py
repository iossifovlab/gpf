import csv
import pysam
import gzip
import os


class MissenseScoresDB:
    chromosomes = map(lambda x: str(x), range(1, 23)) + ['X', 'Y']
    columns = {}

    def __init__(self):
        self.path = os.path.join(os.environ['dbNSFP_PATH'])

        with gzip.open(self.path.format(self.chromosomes[0]), 'rb') as f:
            reader = csv.reader(f, delimiter='\t')
            for i, column in enumerate(reader.next()):
                self.columns[i] = column

        self.tbxs = {chromosome: pysam.Tabixfile(self.path.format(chromosome))
                     for chromosome in self.chromosomes}

    def get_field_names(self):
        return self.columns.values()

    def get_missense_score(self, variant):
        tbx = self.tbxs[variant.chromosome]
        for row in tbx.fetch(variant.chromosome, variant.position - 1,
                             variant.position,  parser=pysam.asTuple()):
            try:
                if (row[2] == variant.reference
                        and row[3] == variant.alternate):
                    return {self.columns[i]: value
                            for i, value in enumerate(row)}
            except ValueError:
                break
