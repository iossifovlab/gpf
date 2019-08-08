from VariantAnnotation import Effect
import subprocess
import csv
import re


class VariantAnnotation(object):
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
        if row[0] == "intronic":
            effect = Effect()
            effect.effect = "intron"
            effect.gene = row[1]
            return [effect]
        elif row[0] == "ncRNA_intronic":
            effect = Effect()
            effect.effect = "non-coding-intron"
            effect.gene = row[1]
            return [effect]
        elif row[0] == "intergenic":
            effect = Effect()
            effect.effect = "intergenic"
            return [effect]
        elif row[0] == "UTR5":
            m = re.match('([a-zA-Z0-9]+)\((.+)\)', row[1])

            effect = Effect()
            effect.effect = "5'UTR"
            effect.gene = m.group(1)
            effect.transcript_id = m.group(2).split(":")[0] + "_1"
            return [effect]
        elif row[0] == "UTR3":
            m = re.match('([a-zA-Z0-9]+)\((.+)\)', row[1])

            effect = Effect()
            effect.effect = "3'UTR"
            effect.gene = m.group(1)
            effect.transcript_id = m.group(2).split(":")[0] + "_1"
            return [effect]
        elif row[0] == "splicing":
            effects = []

            m = re.match('([a-zA-Z0-9]+)\((.+)\)', row[1])
            for details in m.group(2).split(","):
                effect = Effect()
                effect.effect = "splice-site"
                effect.gene = m.group(1)
                effect.transcript_id = details.split(":")[0] + "_1"
                effects.append(effect)
            return effects

        else:
            return []

    @classmethod
    def parse_extron(cls, effect_type, effect_desc):
        print(("AA", effect_desc))
        effect = Effect()
        additional_info = effect_desc.split(":")
        for info in additional_info:
            if info.startswith("p."):
                effect.prot_pos, effect.aa_change = \
                    cls.decode_sequence_variation(info)

        effect.effect = effect_type
        effect.gene = additional_info[0]
        effect.transcript_id = additional_info[1] + "_1"
        return effect

    @classmethod
    def parse_extrons(cls, extron_row):
        print(("BB", extron_row))
        effects_details = [x for x in extron_row[2].split(",") if x]
        effect_type = cls.effect_type_convert(extron_row[1])

        return [cls.parse_extron(effect_type, effect)
                for effect in effects_details]

    @classmethod
    def annotate_variant(cls, gm, refG, chr=None, position=None, loc=None,
                         var=None, ref=None, alt=None, length=None,
                         seq=None, typ=None, promoter_len=0):
        if loc is not None:
            assert(chr is None)
            assert(position is None)
            loc_arr = loc.split(":")
            chr = loc_arr[0]
            position = loc_arr[1]

        if var is not None:
            m = re.match('([a-zA-Z]+)\(([a-zA-Z0-9->]+)\)', var)
            if m.group(1) == "sub":
                sub_m = re.match('([a-zA-Z]+)->([a-zA-Z]+)', m.group(2))
                input_str = "{0}\t{1}\t{1}\t{2}\t{3}".format(chr, position,
                                                             sub_m.group(1),
                                                             sub_m.group(2))
            elif m.group(1) == "del":
                pos_end = int(position) + int(m.group(2)) - 1
                input_str = "{0}\t{1}\t{2}\t0\t-".format(chr, position,
                                                         pos_end)
            elif m.group(1) == "ins":
                input_str = "{0}\t{1}\t{1}\t-\t{2}".format(chr, position,
                                                           m.group(2))
            print(input_str)
        elif ref is not None and alt is not None:
            input_str = "{0}\t{1}\t{1}\t{2}\t{3}".format(chr, position,
                                                         ref, alt)
        else:
            assert(False)

        p = subprocess.Popen(
            ["/home/nikidimi/seqpipe/annovar/annotate_variation.pl", "-out",
             "ex1", "-build", "sep2013", "-", "-hgvs", "-separate",
             "/home/nikidimi/seqpipe/annovar/humandb_Ivan/"],
            stdin=subprocess.PIPE
        )
        p.communicate(input_str)

        with open('ex1.variant_function') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            introns = [effect
                       for row in reader
                       for effect in cls.parse_introns(row)]

        with open('ex1.exonic_variant_function') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            extrons = [effect
                       for row in reader
                       for effect in cls.parse_extrons(row)]

        effects = introns + extrons
        print(effects)
        return effects
