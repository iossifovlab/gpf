import sys
import VariantAnnotation
from .mutation import Mutation, MutatedGenomicSequence


class VariantAnnotator:
    def __init__(self, reference_genome):
        self.reference_genome = reference_genome

    def annotate(self, what_hit, transcript_model, chromosome, pos, length,
                 ref, seq):
        code = VariantAnnotation.NuclearCode()
        codingRegions = transcript_model.CDS_regions()

        ref_length = len(ref)
        seq_length = len(seq)
        length = abs(seq_length - ref_length)
        mutation = Mutation(pos, ref, seq)
        mutated_sequence = MutatedGenomicSequence(self.reference_genome,
                                                  mutation)

        for j in xrange(0, len(codingRegions)):
            if (pos <= codingRegions[j].stop and
                    pos > codingRegions[j].start):
                if length > 0:
                    protPos = self.checkProteinPosition(transcript_model,
                                                        pos, length, "D",
                                                        codingRegions)
                    hit = [transcript_model.gene, protPos]
                    if length % 3 == 0:
                        if self.checkForNewStop(pos, length,
                                                transcript_model,
                                                mutated_sequence,
                                                code) is False:
                            worstEffect = "no-frame-shift"
                        else:
                            worstEffect = "no-frame-shift-newStop"
                        res = [worstEffect, hit, transcript_model.strand,
                               transcript_model.trID]
                        return [res]

                    else:
                        res = ["frame-shift", hit, transcript_model.strand,
                               transcript_model.trID]
                        return [res]

        if what_hit == "intronic":
            hit = [transcript_model.gene, "A", "1", "2/5", "2/5", "10"]
            res = ["non-coding-intron", hit, transcript_model.strand,
                   transcript_model.trID]
            return [res]
        # print(what_hit, transcript_model, pos, length, seq, ref, length)
        # print("COMPLEX")

        s = self.reference_genome.getSequence(chromosome, pos, pos + length)
        # print(s)

        hit = [transcript_model.gene, "Lys", "Lys", "1/100"]
        res = ["synonymous", hit, transcript_model.strand,
               transcript_model.trID]

        return [res]

    def checkProteinPosition(self, tm, pos, length, type, cds_reg):

        codingPos = []
        if type == "D":
            for i in xrange(0, length):
                for j in tm.exons:
                    if (pos + i >= j.start and pos + i <= j.stop
                            and pos + i >= tm.cds[0] and pos + i <= tm.cds[1]):
                        codingPos.append(pos + i)
        else:
            codingPos = [pos]

        minPosCod = codingPos[0]
        maxPosCod = codingPos[-1]

        # protein length
        transcript_length = tm.CDS_len()
        protLength = transcript_length/3 - 1
        if (transcript_length % 3) != 0:
            protLength += 1

        # minAA
        minAA = 0
        # cds_reg = tm.CDS_regions()

        if tm.strand == "+":
            for j in cds_reg:
                if minPosCod >= j.start and minPosCod <= j.stop:
                    minAA += minPosCod - j.start
                    break

                minAA += j.stop-j.start+1
        else:
            for j in cds_reg[::-1]:
                if maxPosCod >= j.start and maxPosCod <= j.stop:
                    minAA += j.stop - maxPosCod
                    break

                minAA += j.stop - j.start + 1
        minAA = minAA/3 + 1

        return(str(minAA) + "/" + str(protLength))

    def checkForNewStop(self, pos, length, tm, mutated_sequence, code):
        if tm.strand == "+":
            frame = self.findFrame(tm, pos)
            if frame == 0:
                return(False)
            if frame == 1:
                codon = self.findCodingBase(tm, pos, -1) + \
                        self.findCodingBase(tm, pos, length) + \
                        self.findCodingBase(tm, pos, length+1)
            else:
                codon = self.findCodingBase(tm, pos, -2) + \
                        self.findCodingBase(tm, pos, -1) + \
                        self.findCodingBase(tm, pos, length)
        else:
            frame = self.findFrame(tm, pos + length - 1)
            if frame == 0:
                return(False)
            if frame == 1:
                codon = self.findCodingBase(tm, pos, length) + \
                        self.findCodingBase(tm, pos, -1) + \
                        self.findCodingBase(tm, pos, -2)
                codon = self.complement(codon)
            else:
                codon = self.findCodingBase(tm, pos, length+1) + \
                        self.findCodingBase(tm, pos, length) + \
                        self.findCodingBase(tm, pos, -1)
                codon = self.complement(codon)
        print(frame, codon)

        start_pos = pos - 2
        seq = mutated_sequence.get_mutated_sequence("1", start_pos,
                                                    start_pos + 2)
        print(self.complement(seq[::-1]))
        if self._in_stop_codons(codon, code):
            return(True)
        return(False)

    def findFrame(self, tm, pos):

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

    def findCodingBase(self, tm, pos, dist):

        if dist == 0:
            return self.reference_genome.getSequence(tm.chr, pos, pos)

        for e in xrange(0, len(tm.exons)):
            if pos >= tm.exons[e].start and pos <= tm.exons[e].stop:
                if (pos+dist >= tm.exons[e].start
                        and pos+dist <= tm.exons[e].stop):
                    return self.reference_genome.getSequence(tm.chr,
                                                             pos + dist,
                                                             pos + dist)
                if dist < 0:
                    d = pos - tm.exons[e].start + dist + 1
                    try:
                        return(self.findCodingBase(tm, tm.exons[e-1].stop, d))
                    except:
                        return("NA")
                else:
                    d = tm.exons[e].stop - pos + dist - 1
                    try:
                        return(self.findCodingBase(tm, tm.exons[e+1].start, d))
                    except:
                        return("NA")
        return(None)

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

    def _in_stop_codons(self, s, code):
        if s in code.stopCodons:
            return True
        else:
            return False
