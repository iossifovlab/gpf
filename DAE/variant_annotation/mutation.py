import logging
import sys


class BaseGenomicSequence(object):
    def __init__(self, annotator, variant, transcript_model):
        self.annotator = annotator
        self.variant = variant
        self.transcript_model = transcript_model
        self.logger = logging.getLogger(__name__)

    def get_coding_region_for_pos(self, pos):
        for i, reg in enumerate(self.transcript_model.exons):
            if reg.start <= pos <= reg.stop:
                return i

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


class PositiveStrandGenomicSequence(BaseGenomicSequence):
    def __init__(self, annotator, variant, transcript_model):
        BaseGenomicSequence.__init__(self, annotator, variant,
                                     transcript_model)

    def get_frame(self, pos, index):
        reg = self.transcript_model.exons[index]
        if reg.stop < self.transcript_model.cds[0]:
            self.logger.error("Cannot detect frame. \
                              Start of coding regions is after current region")
            return 0
        start_pos = max(self.transcript_model.cds[0], reg.start)
        frame = (pos - start_pos + reg.frame) % 3
        self.logger.debug("frame %d for pos=%s", frame, pos)
        return frame

    def get_codons(self):
        index = self.get_coding_region_for_pos(self.variant.position)
        frame = self.get_frame(self.variant.position, index)
        length = max(1, len(self.variant.reference))
        length += self.get_nucleotides_count_to_full_codon(length + frame)

        coding_before_pos = self.get_coding_left(self.variant.position - 1,
                                                 frame, index)
        coding_after_pos = self.get_coding_right(self.variant.position,
                                                 length, index)

        ref_codons = coding_before_pos + coding_after_pos

        length_alt = self.get_nucleotides_count_to_full_codon(
            len(self.variant.alternate) + frame
        )
        alt_codons = coding_before_pos + self.variant.alternate

        if (len(alt_codons) + length_alt == 0):
            length_alt = 3

        alt_codons += self.get_coding_right(
            self.variant.position + len(self.variant.reference),
            length_alt, index
        )
        self.logger.debug("ref codons=%s, alt codons=%s",
                          ref_codons, alt_codons)
        return ref_codons, alt_codons

    def get_amino_acids(self):
        ref_codons, alt_codons = self.get_codons()

        ref_amino_acids = [self.cod2aa(ref_codons[i:i+3])
                           for i in range(0, len(ref_codons), 3)]

        alt_amino_acids = [self.cod2aa(alt_codons[i:i+3])
                           for i in range(0, len(alt_codons), 3)]

        return ref_amino_acids, alt_amino_acids


class NegativeStrandGenomicSequence(BaseGenomicSequence):
    def __init__(self, annotator, variant, transcript_model):
        BaseGenomicSequence.__init__(self, annotator, variant,
                                     transcript_model)

    def get_frame(self, pos, index):
        reg = self.transcript_model.exons[index]
        if reg.start > self.transcript_model.cds[1]:
            self.logger.error("Cannot detect frame. \
                              Start of coding regions is after current region")
            return 0
        stop_pos = min(self.transcript_model.cds[1], reg.stop)
        frame = (stop_pos - pos + reg.frame) % 3
        self.logger.debug("frame %d for pos=%s", frame, pos)
        return frame

    def get_codons(self):
        index = self.get_coding_region_for_pos(self.variant.position)
        frame = self.get_frame(self.variant.position, index)
        length = max(1, len(self.variant.reference))
        length += self.get_nucleotides_count_to_full_codon(length + frame)

        coding_before_pos = self.get_coding_left(self.variant.position,
                                                 length, index)
        coding_after_pos = self.get_coding_right(self.variant.position + 1,
                                                 frame, index)

        ref_codons = coding_before_pos + coding_after_pos

        length_alt = self.get_nucleotides_count_to_full_codon(
            len(self.variant.alternate) + frame
        )
        alt_codons = self.variant.alternate + coding_after_pos

        if (len(alt_codons) + length_alt == 0):
            length_alt = 3

        alt_codons = self.get_coding_left(
            self.variant.position - len(self.variant.reference),
            length_alt, index
        ) + alt_codons

        self.logger.debug("ref codons=%s, alt codons=%s",
                          ref_codons, alt_codons)
        return ref_codons, alt_codons

    @staticmethod
    def complement(nts):
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
        return(reversed)

    def cod2aa(self, codon):
        complement_codon = self.complement(codon[::-1])
        self.logger.debug("complement codon %s for codon %s",
                          complement_codon, codon)
        return BaseGenomicSequence.cod2aa(self, complement_codon)

    def get_amino_acids(self):
        ref_codons, alt_codons = self.get_codons()

        ref_amino_acids = [self.cod2aa(ref_codons[i-3:i])
                           for i in range(len(ref_codons), 0, -3)]

        alt_amino_acids = [self.cod2aa(alt_codons[i-3:i])
                           for i in range(len(alt_codons), 0, -3)]

        return ref_amino_acids, alt_amino_acids


class GenomicSequenceFactory():
    @staticmethod
    def create_genomic_sequence(annotator, variant, transcript_model):
        if transcript_model.strand == "+":
            return PositiveStrandGenomicSequence(annotator, variant,
                                                 transcript_model)
        else:
            return NegativeStrandGenomicSequence(annotator, variant,
                                                 transcript_model)
