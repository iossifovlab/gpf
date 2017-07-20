import subprocess
from ..simple_effect import SimpleEffect


class JannovarVariantAnnotation:
    def __init__(self, reference_genome):
        self.reference_genome = reference_genome

    def annotate(self, variant):
        pos = variant.position
        ref = variant.reference
        alt = variant.alternate

        if len(variant.alternate) == 0:
            pos -= 1
            ref_seq = self.reference_genome.getSequence(variant.chromosome,
                                                        pos, pos)
            alt = ref_seq
            ref = ref_seq + ref

        elif len(variant.reference) == 0:
            pos -= 1
            ref_seq = self.reference_genome.getSequence(variant.chromosome,
                                                        pos, pos)
            ref = ref_seq
            alt = ref_seq + alt

        input_str = "chr{0}:{1}{2}>{3}".format(variant.chromosome, pos,
                                               ref, alt)
        print("j", input_str)
        p = subprocess.Popen(
            ["java", "-jar",
             "jannovar-cli/target/jannovar-cli-0.23-SNAPSHOT.jar",
             "annotate-pos", "-d", "data/hg19_refseq.ser",
             "-c", input_str,
             "--3-letter-amino-acids"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd="/home/nikidimi/seqpipe/jannovar"
        )
        outdata, outerror = p.communicate()
        effects = []

        if p.returncode != 0:
            raise RuntimeError(outerror)

        for line in outdata.split("\n"):
            if len(line) == 0 or line[0] == "#":
                continue
            effect = SimpleEffect(line.split("\t")[1], line.replace("\t", ","))
            effects.append(effect)
        return effects
