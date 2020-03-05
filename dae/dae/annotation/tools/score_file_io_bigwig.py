import pyBigWig


class BigWigLineAdapter:
    def __init__(self, score_file, chromosome, line):
        self.chromosome = chromosome
        self.line = line

        self.chr_index = score_file.chr_index
        self.pos_begin_index = score_file.pos_begin_index
        self.pos_end_index = score_file.pos_end_index

    @property
    def pos_begin(self):
        return self.line[0] + 1  # adjust for bigWig's 0-based positions

    @property
    def pos_end(self):
        return self.line[1]

    @property
    def chrom(self):
        return self.chromosome

    def __getitem__(self, index):
        if index == 0:
            return self.chromosome
        elif index == 1:
            return self.pos_begin
        else:
            return self.line[index - 1]


class BigWigAccess(object):
    def __init__(self, score_file):
        self.score_file = score_file
        self.bwfile = pyBigWig.open(score_file.score_filename)
        assert self.bwfile

    def _cleanup(self):
        self.bwfile.close()

    def _fetch(self, chrom, pos_begin, pos_end):
        assert pos_begin - 1 >= 0
        result = []
        try:
            score_values = self.bwfile.intervals(chrom, pos_begin - 1, pos_end)
            if score_values:
                for line in score_values:
                    result.append(
                        BigWigLineAdapter(self.score_file, chrom, line)
                    )
        except RuntimeError:
            pass  # no scores found by the intervals() method
        return result
