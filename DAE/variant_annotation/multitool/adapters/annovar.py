from ..simple_effect import SimpleEffect
import subprocess
import csv
import re
from .base import BaseAdapter


class AnnovarVariantAnnotation(BaseAdapter):
    @staticmethod
    def amino_acids_decode(code):
        amino_acids_dict = {
            'R': 'Arg',
            'H': 'His',
            'K': 'Lys',
            'D': 'Asp',
            'E': 'Glu',
            'S': 'Ser',
            'T': 'Thr',
            'N': 'Asn',
            'Q': 'Gln',
            'C': 'Cys',
            'U': 'Sec',
            'G': 'Gly',
            'P': 'Pro',
            'A': 'Ala',
            'V': 'Val',
            'I': 'Ile',
            'L': 'Leu',
            'M': 'Met',
            'F': 'Phe',
            'Y': 'Tyr',
            'W': 'Trp',
            'X': 'End'
        }
        return amino_acids_dict[code]

    @classmethod
    def decode_sequence_variation(cls, sequence_variation_desc):
        aa_change = None
        pos = None

        try:
            m = re.match('p.([A-Z])([0-9_]+)([a-zA-Z]+)',
                         sequence_variation_desc)
            pos = int(m.group(2))

            a = cls.amino_acids_decode(m.group(1))
            b = cls.amino_acids_decode(m.group(3))
            aa_change = "{}->{}".format(a, b)
        except KeyError:
            pass
        except AttributeError:
            pass

        return pos, aa_change

    @staticmethod
    def effect_type_convert(code):
        effect_types_dict = {
            'synonymous SNV': 'synonymous',
            'nonsynonymous SNV': 'missense',
            'frameshift deletion': 'frame-shift',
            'frameshift substitution': 'frame-shift',
            'frameshift insertion': 'frame-shift',
            'nonframeshift deletion': 'no-frame-shift',
            'stopgain': 'nonsense'
        }

        if code in effect_types_dict:
            return effect_types_dict[code]
        return code

    @classmethod
    def parse_introns(cls, row):
        print(row[0])
        if row[0] != "exonic":
            effect = SimpleEffect(row[0], ",".join(row))
            effect.details = row
            return [effect]
        else:
            return []

    @classmethod
    def parse_extron(cls, effect_type, effect_desc):
        effect = SimpleEffect(effect_type, effect_desc)
        return effect

    @classmethod
    def parse_extrons(cls, extron_row):
        print(("BB", extron_row))
        effects_details = [x for x in extron_row[2].split(",") if x]
        effect_type = cls.effect_type_convert(extron_row[1])

        return [cls.parse_extron(effect_type, effect)
                for effect in effects_details]

    def annotate(self, variant):
        pos = variant.position
        if len(variant.reference) > 0:
            ref = variant.reference
        else:
            ref = "-"
            pos -= 1

        if len(variant.alternate) > 0:
            alt = variant.alternate
        else:
            alt = "-"

        last_pos = pos + len(ref) - 1

        input_str = "{0}\t{1}\t{2}\t{3}\t{4}".format(variant.chromosome,
                                                     pos, last_pos,
                                                     ref, alt)
        print("input_str {}".format(input_str))

        p = subprocess.Popen(
            ["/home/nikidimi/seqpipe/annovar/annotate_variation.pl", "-out",
             "ex1", "-build", "sep2013", "-", "-hgvs", "-separate",
             "/home/nikidimi/seqpipe/annovar/humandb_Ivan/"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        outdata, outerror = p.communicate(input_str)

        if p.returncode != 0:
            raise RuntimeError(outerror)

        with open('ex1.variant_function') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            introns = [effect
                       for row in reader
                       for effect in self.parse_introns(row)]

        with open('ex1.exonic_variant_function') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            extrons = [effect
                       for row in reader
                       for effect in self.parse_extrons(row)]

        effects = introns + extrons
        print(effects)
        return None, effects
