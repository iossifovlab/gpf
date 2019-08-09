import sys


class Mutation(object):
    def __init__(self, pos, ref, alt):
        self.start_position = pos
        self.end_ref_position = pos + len(ref) - 1
        self.end_alt_position = pos + len(alt) - 1
        self.length_diff = len(alt) - len(ref)
        self.ref = ref
        self.alt = alt

    def get_mutated_sequence(self, pos, pos_end):
        print(("GET", pos, pos_end, self.start_position, self.end_alt_position))
        start_position = max(0, pos - self.start_position)
        end_position = pos_end - self.end_alt_position
        print(("MUT", start_position, end_position))
        if end_position < 0:
            return self.alt[start_position:end_position]
        else:
            return self.alt[start_position:]


class GenomicSequence(object):
    def __init__(self, genome_seq):
        self.genome_seq = genome_seq

    def get_sequence(self, chromosome, pos_start, pos_end):
        print(("GETS", pos_start, pos_end))
        if pos_start > pos_end:
            return ""
        return self.genome_seq.getSequence(chromosome, pos_start,
                                           pos_end)


class MutatedGenomicSequence(GenomicSequence):
    def __init__(self, genome_seq, mutation):
        super(MutatedGenomicSequence, self).__init__(genome_seq)
        self.mutation = mutation

    def clamp(self, val, min_val, max_val):
        return min(max_val, max(min_val, val))

    def get_sequence(self, chromosome, pos, pos_end):
        mutation_start = self.clamp(self.mutation.start_position,
                                    pos, pos_end + 1)

        result = super(MutatedGenomicSequence, self).get_sequence(
            chromosome, pos, mutation_start - 1
        )
        result += self.mutation.get_mutated_sequence(pos, pos_end)

        mutation_end = self.clamp(self.mutation.end_alt_position + 1,
                                  pos, pos_end + 1)
        result += super(MutatedGenomicSequence, self).get_sequence(
            chromosome, mutation_end - self.mutation.length_diff,
            pos_end - self.mutation.length_diff
        )

        return result


class TranscriptModelWrapper(object):
    def __init__(self, transcript_model, genome_seq):
        self.transcript_model = transcript_model
        self.genome_seq = genome_seq

    def _find_frame(self, pos):
        tm = self.transcript_model
        if pos < tm.cds[0] or pos > tm.cds[1]:
            return(-1)

        for e in tm.exons:
            if pos >= e.start and pos <= e.stop:
                if tm.cds[0] >= e.start:
                    if tm.strand == "+":
                        return((pos - tm.cds[0] + e.frame) % 3)
                    if tm.cds[1] <= e.stop:
                        return((tm.cds[1] - pos + e.frame) % 3)
                    return((e.stop - pos + e.frame) % 3)
                if tm.cds[1] <= e.stop:
                    if tm.strand == "+":
                        return((pos - e.start + e.frame) % 3)
                    return((tm.cds[1] - pos + e.frame) % 3)

                if tm.strand == "+":
                    return((pos - e.start + e.frame) % 3)
                return((e.stop - pos + e.frame) % 3)

        return(None)

    def get_codon_start_pos(self, pos):
        frame = self._find_frame(pos)
        if self.transcript_model.strand == "+":
            start_pos = pos - frame
        else:
            start_pos = pos + frame
        return start_pos

    def get_codon_for_pos(self, chromosome, pos):
        start_pos = self.get_codon_start_pos(pos)
        print(("start_pos", start_pos))
        if self.transcript_model.strand == "+":
            end_pos = start_pos + 2
            return self.genome_seq.get_sequence(chromosome,
                                                start_pos, end_pos)
        else:
            end_pos = start_pos
            start_pos = end_pos - 2
            codon = self.genome_seq.get_sequence(chromosome,
                                                 start_pos, end_pos)
            print(("reverse", start_pos, end_pos, codon))
            return self.complement(codon[::-1])

    def get_first_codon(self):
        if self.transcript_model.strand == "+":
            pos = self.transcript_model.cds[0]
        else:
            pos = self.transcript_model.cds[1]
        return self.get_codon_for_pos(self.transcript_model.chr, pos)

    def get_last_codon(self):
        if self.transcript_model.strand == "+":
            pos = self.transcript_model.cds[1]
        else:
            pos = self.transcript_model.cds[0]
        print(("LAST CODON", pos))
        return self.get_codon_for_pos(self.transcript_model.chr, pos)

    def complement(self, nts):
        nts = nts.upper()
        reversed = ''
        for nt in nts:
            if nt == "A":
                reversed += "T"
            elif nt == "T":
                reversed += "A"
            elif nt == "G":
                reversed += "C"
            elif nt == "C":
                reversed += "G"
            elif nt == "N":
                reversed += "N"
            else:
                print("Invalid nucleotide: " + str(nt) + " in " + str(nts))
                sys.exit(-23)
        return(reversed)
