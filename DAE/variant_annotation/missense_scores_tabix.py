import csv
import pysam
import gzip
import os


class MissenseScoresDB:
    chromosomes = range(1, 23) + ['M', 'X', 'Y']
    columns = {}

    def __init__(self):
        self.path = os.path.join(os.environ['dbNSFP_PATH'])

        with gzip.open(self.path.format(self.chromosomes[0]), 'rb') as f:
            reader = csv.reader(f, delimiter='\t')
            for i, column in enumerate(reader.next()):
                self.columns[i] = column

    def get_field_names(self):
        return self.columns.values()

    def get_missense_score(self, variant):
        tbx = pysam.Tabixfile(self.path.format(variant.chromosome))
        for row in tbx.fetch(variant.chromosome, variant.position - 1,
                             variant.position,  parser=pysam.asTuple()):
            try:
                if (row[2] == variant.reference
                        and row[3] == variant.alternate):
                    return {self.columns[i]: value
                            for i, value in enumerate(row)}
            except ValueError:
                break
