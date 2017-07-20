class ExonMock:
    def __init__(self, start, stop, frame):
        self.start = start
        self.stop = stop
        self.frame = frame


class TranscriptModelMock:
    def __init__(self, strand, cds_start, cds_end, exons):
        self.strand = strand
        self.cds = [cds_start, cds_end]
        self.exons = exons
        self.chr = "1"
        self.gene = "B"
        self.trID = "123"

    def CDS_regions(self):
        return self.exons


class ReferenceGenomeMock:
    def getSequence(self, chromosome, pos, pos_last):
        print("get", chromosome, pos, pos_last)
        return "".join([chr(i) for i in range(pos, pos_last + 1)])


class AnnotatorMock:
    def __init__(self, reference_genome):
        self.reference_genome = reference_genome
