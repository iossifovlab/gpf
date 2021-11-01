class ExonMock(object):
    def __init__(self, start, stop, frame):
        self.start = start
        self.stop = stop
        self.frame = frame


class TranscriptModelMock(object):
    def __init__(
        self, strand, cds_start, cds_end, exons, coding=None, is_coding=True
    ):
        self.strand = strand
        self.cds = [cds_start, cds_end]
        self.exons = exons
        self.chrom = "1"
        self.gene = "B"
        self.tr_id = "123"
        self.tr_name = "123"

        if coding is None:
            self.coding = self.exons
        else:
            self.coding = coding
        self._is_coding = is_coding

    def CDS_regions(self):
        return self.coding

    def is_coding(self):
        return self._is_coding

    def all_regions(self):
        return self.exons


class ReferenceGenomeMock(object):
    def get_sequence(self, chromosome, pos, pos_last):
        print(("get", chromosome, pos, pos_last))
        return "".join([chr(i) for i in range(pos, pos_last + 1)])


class CodeMock(object):
    startCodons = ["ABC", "DEF"]
    CodonsAaKeys: dict = {}


class AnnotatorMock(object):
    def __init__(self, reference_genome):
        self.reference_genome = reference_genome
        self.code = CodeMock()
