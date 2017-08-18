import csv
import pickle


class MissenseScoresDB:
    PATH = "/home/nikidimi/Data/seqpipe2/dbNSFP3.4a_variant.chr{}"
    chromosomes = range(1, 23) + ['M', 'X', 'Y']
    indexes = {}

    def load_all_indexes(self):
        for chromosome in self.chromosomes:
            self.load_index(chromosome)

    def load_index(self, chromosome):
        with open(self.PATH.format(chromosome) + '.idx', 'rb') as f:
            self.indexes[str(chromosome)] = pickle.load(f)

    def rebuild_all_indexes(self):
        for chromosome in self.chromosomes:
            self.rebuild_index(chromosome)

    def rebuild_index(self, chromosome):
        index = {}
        prev = 0
        with open(self.PATH.format(chromosome), 'rb') as f:
            for line in iter(f.readline, ''):
                try:
                    position = int(line.split()[8])
                    if position not in index:
                        index[position] = prev
                except ValueError:
                    pass
                prev = f.tell()

        with open(self.PATH.format(chromosome) + '.idx', 'wb') as f:
            pickle.dump(index, f, pickle.HIGHEST_PROTOCOL)

    def get_field_names(self):
        with open(self.PATH.format(self.chromosomes[0]), 'rb') as f:
            reader = csv.reader(f, delimiter='\t')
            return reader.next()[15:]

    def get_missense_score(self, variant):
        with open(self.PATH.format(variant.chromosome), 'rb') as f:
            if variant.position not in self.indexes[variant.chromosome]:
                return None
            f.seek(self.indexes[variant.chromosome][variant.position])
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                try:
                    if int(row[8]) != variant.position:
                        break

                    if (row[2] == variant.reference
                            and row[3] == variant.alternate):
                        return row[15:]
                except ValueError:
                    break
