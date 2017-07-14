import sys


class GenomicSequence(object):
    def __init__(self, annotator, variant, transcript_model):
        self.annotator = annotator
        self.variant = variant
        self.transcript_model = transcript_model

    def get_coding_region_for_pos(self, pos):
        for i, reg in enumerate(self.transcript_model.exons):
            if reg.start <= pos <= reg.stop:
                return i

    def get_frame(self, pos, index):
        reg = self.transcript_model.exons[index]
        return((pos - reg.start + reg.frame) % 3)

    def get_coding_right(self, pos, length, index):
        if length <= 0:
            return ""

        reg = self.transcript_model.exons[index]

        if pos == -1:
            pos = reg.start
        last_index = min(pos + length - 1, reg.stop)
        seq = self.annotator.reference_genome.getSequence(
            self.transcript_model.chr, pos, last_index
        )

        length -= len(seq)
        return seq + self.get_coding_right(-1, length, index + 1)

    def get_coding_left(self, pos, length, index):
        if length <= 0:
            return ""

        reg = self.transcript_model.exons[index]

        if pos == -1:
            pos = reg.stop
        start_index = max(pos - length + 1, reg.start)
        seq = self.annotator.reference_genome.getSequence(
            self.transcript_model.chr, start_index, pos
        )

        length -= len(seq)
        return self.get_coding_left(-1, length, index - 1) + seq

    def get_nucleotides_count_to_full_codon(self, length):
        return (3 - (length % 3)) % 3

    def get_codons(self):
        index = self.get_coding_region_for_pos(self.variant.position)
        frame = self.get_frame(self.variant.position, index)
        length = len(self.variant.reference)
        length += self.get_nucleotides_count_to_full_codon(
            len(self.variant.reference) + frame
        )

        coding_before_pos = self.get_coding_left(self.variant.position - 1,
                                                 frame, index)
        coding_after_pos = self.get_coding_right(self.variant.position,
                                                 length, index)

        ref_codons = coding_before_pos + coding_after_pos

        length_alt = self.get_nucleotides_count_to_full_codon(
            len(self.variant.alternate) + frame
        )
        alt_codons = coding_before_pos + self.variant.alternate
        alt_codons += self.get_coding_right(
            self.variant.position + len(self.variant.reference),
            length_alt, index
        )
        return ref_codons, alt_codons

    def cod2aa(self, codon):
        codon = codon.upper()
        if len(codon) != 3:
            return("?")

        for i in codon:
            if i not in ['A', 'C', 'T', 'G', 'N']:
                print("Codon can only contain: A, G, C, T, N letters, \
                      this codon is: " + codon)
                sys.exit(-21)
            if i == "N":
                return("?")

        for key in self.annotator.code.CodonsAaKeys:
            if codon in self.annotator.code.CodonsAa[key]:
                return(key)

        return(None)

    def get_amino_acids(self):
        ref_codons, alt_codons = self.get_codons()

        ref_amino_acids = [self.cod2aa(ref_codons[i:i+3])
                           for i in range(0, len(ref_codons), 3)]

        alt_amino_acids = [self.cod2aa(alt_codons[i:i+3])
                           for i in range(0, len(alt_codons), 3)]

        return ref_amino_acids, alt_amino_acids
