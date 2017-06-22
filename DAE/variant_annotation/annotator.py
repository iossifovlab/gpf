class VariantAnnotator:
    def __init__(self, reference_genome):
        self.reference_genome = reference_genome

    def annotate(self, what_hit, transcript_model, chromosome, pos, length,
                 ref, seq):
        codingRegions = transcript_model.CDS_regions()

        ref_length = len(ref)
        seq_length = len(seq)
        length = abs(seq_length - ref_length)

        for j in xrange(0, len(codingRegions)):
            if (pos <= codingRegions[j].stop and
                    pos > codingRegions[j].start):
                if length > 0:
                    hit = [transcript_model.gene, "1/100"]
                    if length % 3 == 0:
                        res = ["no-frame-shift", hit, transcript_model.strand,
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
        #print(what_hit, transcript_model, pos, length, seq, ref, length)
        #print("COMPLEX")

        s = self.reference_genome.getSequence(chromosome, pos, pos + length)
        #print(s)

        hit = [transcript_model.gene, "Lys", "Lys", "1/100"]
        res = ["synonymous", hit, transcript_model.strand,
               transcript_model.trID]

        return [res]
