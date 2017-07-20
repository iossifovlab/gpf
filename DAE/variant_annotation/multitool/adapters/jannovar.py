import subprocess
from ..simple_effect import SimpleEffect


class JannovarVariantAnnotation:
    def annotate(self, variant):
        if len(variant.reference) > 0:
            ref = variant.reference
        else:
            ref = "-"

        if len(variant.alternate) > 0:
            alt = variant.alternate
        else:
            alt = "-"

        input_str = "chr{0}:{1}{2}>{3}".format(variant.chromosome,
                                               variant.position,
                                               ref, alt)

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

        for line in outdata.split("\n"):
            if len(line) == 0 or line[0] == "#":
                continue
            effect = SimpleEffect(line.split("\t")[1], line.replace("\t", ","))
            effects.append(effect)
        return effects
