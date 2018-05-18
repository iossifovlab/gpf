from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
import sys
import VariantAnnotation
from .mutation import Mutation, MutatedGenomicSequence, TranscriptModelWrapper
from .mutation import GenomicSequence


class VariantAnnotator(object):
    def __init__(self, transcript_model, pos, ref, seq,
                 reference_genome, code):
        self.transcript_model = transcript_model
        self.reference_genome = reference_genome
        self.code = code
        self.mutation = Mutation(pos, ref, seq)

        self.ref_sequence = GenomicSequence(self.reference_genome)
        self.alt_sequence = MutatedGenomicSequence(self.reference_genome,
                                                   self.mutation)

        self.ref_model = TranscriptModelWrapper(self.transcript_model,
                                                self.ref_sequence)
        self.alt_model = TranscriptModelWrapper(self.transcript_model,
                                                self.alt_sequence)

    def firstOrLastCodonOutput_Indel(self, tm, pos, worstEffect,
                                     type, cds_reg, length):
        if worstEffect == "no-frame-shift" or worstEffect == "frame-shift":
            protPos = VariantAnnotation.checkProteinPosition(
                tm, pos, length, type, cds_reg
            )
            hit = [tm.gene, protPos]
        elif worstEffect == "noEnd" or worstEffect == "noStart":
            protLength = old_div(tm.CDS_len(),3)
            hit = [tm.gene, str(protLength)]
        elif worstEffect == "3'UTR" or worstEffect == "5'UTR":
            d = VariantAnnotation.distanceFromCoding(pos, tm)
            hit = [worstEffect, [tm.gene, worstEffect, str(d)]]

        else:
            print("incorrect mut type: " + worstEffect)
            sys.exit(-233)

        return([worstEffect, hit])

    def dealWithLastCodon_Del(self, tm, pos, length, cds_reg):
        codon = self.ref_model.get_last_codon()
        mutated_codon = self.alt_model.get_last_codon()

        print(("LAST_DEL", codon, mutated_codon, pos))
        if (self._in_stop_codons(codon) and
                not self._in_stop_codons(mutated_codon)):
            worstEffect = "noEnd"
        else:
            return None

        out = self.firstOrLastCodonOutput_Indel(tm, pos, worstEffect, "D",
                                                cds_reg, length)
        return out

    def dealWithCodingAndLastCodon_Del(self, tm, pos, length, cds_reg):
        if tm.strand == "+":
            if pos + length - 1 <= tm.cds[1]:
                if length % 3 != 0:
                    worstEffect = "frame-shift"
                else:
                    worstEffect = "no-frame-shift"
            else:
                worstEffect = "noEnd"

        else:
            if pos + length - 1 > tm.cds[1]:
                length = tm.cds[1] - pos + 1
            if length % 3 != 0:
                worstEffect = "frame-shift"
            else:
                worstEffect = "noStart"

        out = self.firstOrLastCodonOutput_Indel(tm, pos, worstEffect, "D",
                                                cds_reg, length)
        return(out)

    def dealWithFirstCodon_Del(self, tm, pos, length, cds_reg):
        codon = self.ref_model.get_first_codon()
        mutated_codon = self.alt_model.get_first_codon()

        print(("FIRST_DEL", codon, mutated_codon, pos))

        if (self._in_start_codons(codon) and
                not self._in_start_codons(mutated_codon)):
            worstEffect = "noStart"
        else:
            return None

        out = self.firstOrLastCodonOutput_Indel(tm, pos, worstEffect, "D",
                                                cds_reg, length)
        return(out)

    def splice_check(self, seq, chromosome, pos, pos_last, length,
                     codingRegions):
        worstEffect = None

        prev = codingRegions[0].stop
        for j in codingRegions:
            if length == 0:
                if pos < j.start and pos > prev:
                    if pos - prev < 3 or j.start - pos < 3:
                        # splice
                        worstEffect = "splice-site"
                    else:
                        # intron not splice
                        worstEffect = "intron"

                    hit = VariantAnnotation.prepareIntronHit(
                        self.transcript_model, pos, 1, codingRegions)
                    if worstEffect == "splice-site":
                        c = VariantAnnotation.findSpliceContext(
                            self.transcript_model, pos, length, seq,
                            codingRegions, "S", self.reference_genome
                        )
                        hit.append(c)
                    return [[worstEffect, hit, self.transcript_model.strand,
                             self.transcript_model.trID]]

                    break
            print(("A", pos, pos_last, j.start, prev))
            if (pos < j.start and pos > prev) or \
                    (pos_last < j.start and pos_last > prev):
                print("SPLICE SITE CHECK")
                for s in [prev + 1, prev+2, j.start-1, j.start-2]:
                    if pos <= s <= pos_last:
                        if s == prev + 1 or s == prev+2:
                            splice = (prev + 1, prev + 2)
                            side = "5'"
                        else:
                            splice = (j.start-2, j.start-1)
                            side = "3'"
                        worstEffect = self.checkIfSplice(
                            chromosome, pos, None, length, splice, side,
                        )

                        if worstEffect == "splice-site":
                            hit = VariantAnnotation.prepareIntronHit(
                                self.transcript_model, pos, length,
                                codingRegions
                            )

                            c = VariantAnnotation.findSpliceContext(
                                self.transcript_model, pos, length, seq,
                                codingRegions, "D", self.reference_genome
                            )
                            hit.append(c)

                        elif worstEffect == "intron":
                            print("INTRON HIT??")
                            hit = VariantAnnotation.prepareIntronHit(
                                self.transcript_model, pos, length,
                                codingRegions
                            )
                        elif worstEffect == "frame-shift" \
                                or worstEffect == "no-frame-shift":
                            protPos = VariantAnnotation.checkProteinPosition(
                                self.transcript_model, pos, length, "D",
                                codingRegions
                            )
                            hit = [self.transcript_model.gene, protPos]
                        else:
                            print("No such worst effect type: " + worstEffect)
                            sys.exit(-65)
                        break
                if worstEffect is None:
                    hit = VariantAnnotation.prepareIntronHit(
                        self.transcript_model, pos, length, codingRegions
                    )
                    print("INTRON HIT 2??")
                    worstEffect = "intron"

                return [[worstEffect, hit, self.transcript_model.strand,
                         self.transcript_model.trID]]
            prev = j.stop
        return None

    def annotate(self, what_hit, pos, length, ref, seq):
        codingRegions = self.transcript_model.CDS_regions()

        ref_length = len(ref)
        seq_length = len(seq)
        length = abs(seq_length - ref_length)
        try:
            codon = self.ref_model.get_codon_for_pos(
                self.transcript_model.chr, pos
            )
            mutated_codon = self.alt_model.get_codon_for_pos(
                self.transcript_model.chr, pos
            )

            print("codon change: {}->{}".format(codon, mutated_codon))
        except TypeError:
            print("codon change N/A")

        if length == 0:
            pos_last = pos
        else:
            pos_last = pos + length - 1

        worstEffect = None
        worstForEachTranscript = []
        print(("START", codingRegions, pos, pos_last))

        splice_check = self.splice_check(seq, self.transcript_model.chr,
                                         pos, pos_last, length, codingRegions)
        if splice_check is not None:
            return splice_check

        if self.transcript_model.strand == "+":
            tm = self.transcript_model
            print(("TX", pos, tm.cds[1], tm.tx[1]))
            if pos >= tm.cds[0] and pos <= tm.cds[0] + 2:
                if tm.cds[0] == tm.tx[0]:
                    return [["5'UTR", [tm.gene, "5'UTR", "1"],
                             tm.strand, tm.trID]]
            if pos >= tm.cds[1] - 2 and pos <= tm.cds[1]:
                if tm.cds[1] == tm.tx[1]:
                    return [["3'UTR", [tm.gene, "3'UTR", "1"],
                             tm.strand, tm.trID]]

            if pos < self.transcript_model.cds[0] + 3:

                h = self.dealWithFirstCodon_Del(
                    self.transcript_model, pos, length, codingRegions
                )
                if h is not None:
                    h.append(self.transcript_model.strand)
                    h.append(self.transcript_model.trID)
                    worstForEachTranscript.append(h)
                    return worstForEachTranscript

            if pos > self.transcript_model.cds[1] - 3 \
                    and pos <= self.transcript_model.cds[1]:
                h = self.dealWithLastCodon_Del(
                    self.transcript_model, pos, length, codingRegions
                )
                if h is not None:
                    h.append(self.transcript_model.strand)
                    h.append(self.transcript_model.trID)
                    worstForEachTranscript.append(h)
                    return worstForEachTranscript
        else:
            tm = self.transcript_model
            print(("TX REV", pos, tm.cds[1], tm.tx[1]))
            if pos >= tm.cds[0] and pos <= tm.cds[0] + 2:
                if tm.cds[0] == tm.tx[0]:
                    return [["3'UTR", [tm.gene, "3'UTR", "1"],
                             tm.strand, tm.trID]]
            if pos >= tm.cds[1] - 2 and pos <= tm.cds[1]:
                if tm.cds[1] == tm.tx[1]:
                    return [["5'UTR", [tm.gene, "5'UTR", "1"],
                             tm.strand, tm.trID]]

            if pos > self.transcript_model.cds[1] - 3 \
                    and pos <= self.transcript_model.cds[1]:

                h = self.dealWithFirstCodon_Del(
                    self.transcript_model, pos, length, codingRegions,
                )
                if h is not None:
                    h.append(self.transcript_model.strand)
                    h.append(self.transcript_model.trID)
                    worstForEachTranscript.append(h)
                    return worstForEachTranscript

            if pos < self.transcript_model.cds[0] + 3:
                h = self.dealWithLastCodon_Del(
                    self.transcript_model, pos, length, codingRegions
                )
                if h is not None:
                    h.append(self.transcript_model.strand)
                    h.append(self.transcript_model.trID)
                    worstForEachTranscript.append(h)
                    return worstForEachTranscript

        if pos <= self.transcript_model.cds[1] - 3 \
                and pos_last > self.transcript_model.cds[1] - 3:
            h = self.dealWithCodingAndLastCodon_Del(
                self.transcript_model, pos, length, codingRegions
            )
            h.append(self.transcript_model.strand)
            h.append(self.transcript_model.trID)
            worstForEachTranscript.append(h)
            return worstForEachTranscript

        for j in codingRegions:
            if (pos <= j.stop or
                    pos >= j.start):
                if length > 0:
                    protPos = VariantAnnotation.checkProteinPosition(
                        self.transcript_model, pos, length, "D", codingRegions
                    )
                    hit = [self.transcript_model.gene, protPos]
                    if length % 3 == 0:
                        if self.checkForNewStop(pos, length) is False:
                            worstEffect = "no-frame-shift"
                        else:
                            worstEffect = "no-frame-shift-newStop"
                        res = [worstEffect, hit, self.transcript_model.strand,
                               self.transcript_model.trID]
                        worstForEachTranscript.append(res)
                        return worstForEachTranscript

                    else:
                        res = ["frame-shift", hit,
                               self.transcript_model.strand,
                               self.transcript_model.trID]
                        worstForEachTranscript.append(res)
                        return worstForEachTranscript
                elif length == 0:
                        refAA = self.cod2aa(codon)
                        altAA = self.cod2aa(mutated_codon)

                        worstEffect = self.mutationType(refAA, altAA)
                        protPos = VariantAnnotation.checkProteinPosition(
                            tm, pos, length, "S", codingRegions
                        )
                        hit = [self.transcript_model.gene, refAA, altAA,
                               protPos]
                        worstForEachTranscript.append(
                            [worstEffect, hit, self.transcript_model.strand,
                             self.transcript_model.trID]
                        )
                        return worstForEachTranscript
        return worstForEachTranscript

    def checkForNewStop(self, pos_start, length):
        for pos in range(pos_start, pos_start + length):
            codon = self.ref_model.get_codon_for_pos(
                self.transcript_model.chr, pos
            )
            mutated_codon = self.alt_model.get_codon_for_pos(
                self.transcript_model.chr, pos
            )

            print(("checkForNewStop", pos, codon, mutated_codon))

            if self._in_stop_codons(mutated_codon) and \
                    not self._in_stop_codons(codon):
                return True
        return False

    def _in_stop_codons(self, s):
        if s in self.code.stopCodons:
            return True
        else:
            return False

    def _in_start_codons(self, s):
        if s in self.code.startCodons:
            return True
        else:
            return False

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

        for key in self.code.CodonsAaKeys:
            if codon in self.code.CodonsAa[key]:
                return(key)

        return(None)

    def mutationType(self, aaref, aaalt):

        if aaref == aaalt and aaref != "?":
            return("synonymous")
        if aaalt == 'End':
            return("nonsense")
        if aaref == "?" or aaalt == "?":
            return("coding_unknown")

        return("missense")

    def checkIfSplice(self, chrom, pos, seq, length, splicePos, side):
        splice_seq = self.reference_genome.getSequence(chrom, splicePos[0],
                                                       splicePos[1])
        print(("checkIfSplice_new", chrom, pos, seq, length, splicePos, side,
              splice_seq))
        if side == "5'":
            # prev
            if pos < splicePos[0]:
                if (splicePos[0] - pos) % 3 != 0:
                    worstEffect = "frame-shift"
                else:
                    if pos+length-1 >= splicePos[1]:
                        if self.reference_genome.getSequence(
                            chrom, pos+length, pos+length+1
                        ) == splice_seq:
                            worstEffect = "no-frame-shift"
                        else:
                            worstEffect = "splice-site"
                    else:
                        worstEffect = "splice-site"
            elif pos == splicePos[0]:
                if length == 1:
                    worstEffect = "splice-site"
                else:
                    if self.reference_genome.getSequence(
                        chrom, pos+length, pos+length+1
                    ) == splice_seq:
                        worstEffect = "intron"
                    else:
                        worstEffect = "splice-site"
            elif pos == splicePos[1]:
                if self.reference_genome.getSequence(
                    chrom, pos+length, pos+length
                ) == splice_seq[1]:
                    worstEffect = "intron"
                else:
                    worstEffect = "splice-site"
            else:
                print("Something's wrong in checkIfSplice")
                print((pos, splicePos))
                sys.exit(-81)
        else:
            # side "3'"
            if pos <= splicePos[0]:
                if pos + length - 1 >= splicePos[1]:
                    if self.reference_genome.getSequence(
                        chrom, pos-2, pos-1
                    ) == splice_seq:
                        if pos + length - 1 > splicePos[1]:
                            if (splicePos[1] - pos + length - 1) % 3 == 0:
                                worstEffect = "no-frame-shift"
                            else:
                                worstEffect = "frame-shift"
                        else:
                            worstEffect = "intron"
                    else:
                        worstEffect = "splice-site"

                else:
                    worstEffect = "splice-site"

            elif pos == splicePos[1]:
                if self.reference_genome.getSequence(
                    chrom, pos-1, pos-1
                ) == splice_seq[1]:
                    if length > 1:
                        if (length - 1) % 3 == 0:
                            worstEffect = "no-frame-shift"
                        else:
                            worstEffect = "frame-shift"
                    else:
                        worstEffect = "intron"
                else:
                    worstEffect = "splice-site"
            else:
                print("Something's wrong in checkIfSplice")
                print((pos, splicePos))
                sys.exit(-82)

        return(worstEffect)
