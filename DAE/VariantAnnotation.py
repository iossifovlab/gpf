#!/bin/env python

# October 25th 2013
# written by Ewa

import sys
import re
from GeneModelFiles import *
from variant_annotation.annotator import VariantAnnotator


Severity = {
    'tRNA:ANTICODON': 30,
    'all': 24,
    'splice-site': 23,
    'frame-shift': 22,
    'nonsense': 21,
    'no-frame-shift-newStop': 20,
    'noStart': 19,
    'noEnd': 18,
    'missense': 17,
    'no-frame-shift': 16,
    'CDS': 15,
    'synonymous': 14,
    'coding_unknown': 13,
    'regulatory': 12,
    "3'UTR": 11,
    "5'UTR": 10,
    'intron': 9,
    'non-coding': 8,
    "5'UTR-intron": 7,
    "3'UTR-intron": 6,
    "promoter": 5,
    "non-coding-intron": 4,
    'unknown': 3,
    'intergenic': 2,
    'no-mutation': 1
}

LOF = ['splice-site', 'frame-shift', 'nonsense', 'no-frame-shift-newStop']
nonsyn = ['splice-site', 'frame-shift', 'nonsense', 'no-frame-shift-newStop',
          'missense', 'noStart', 'noEnd', 'no-frame-shift']


class NuclearCode:

    stopCodons = ['TAG', 'TAA', 'TGA']
    startCodons = ['ATG']

    CodonsAa = {
        'Gly': ['GGG', 'GGA', 'GGT', 'GGC'],
        'Glu': ['GAG', 'GAA'],
        'Asp': ['GAT', 'GAC'],
        'Val': ['GTG', 'GTA', 'GTT', 'GTC'],
        'Ala': ['GCG', 'GCA', 'GCT', 'GCC'],
        'Arg': ['AGG', 'AGA', 'CGG', 'CGA', 'CGT', 'CGC'],
        'Ser': ['AGT', 'AGC', 'TCG', 'TCA', 'TCT', 'TCC'],
        'Lys': ['AAG', 'AAA'],
        'Asn': ['AAT', 'AAC'],
        'Met': startCodons,
        'Ile': ['ATA', 'ATT', 'ATC'],
        'Thr': ['ACG', 'ACA', 'ACT', 'ACC'],
        'Trp': ['TGG'],
        'End': stopCodons,
        'Cys': ['TGT', 'TGC'],
        'Tyr': ['TAT', 'TAC'],
        'Leu': ['TTG', 'TTA', 'CTG', 'CTA', 'CTT', 'CTC'],
        'Phe': ['TTT', 'TTC'],
        'Gln': ['CAG', 'CAA'],
        'His': ['CAT', 'CAC'],
        'Pro': ['CCG', 'CCA', 'CCT', 'CCC']
    }

    CodonsAaKeys = CodonsAa.keys()


class MitochondrialCode:

    stopCodons = ['TAA', 'TAG']
    startCodons = ['ATG', 'ATA']

    CodonsAa = {
        'Gly': ['GGG', 'GGA', 'GGT', 'GGC'],
        'Glu': ['GAG', 'GAA'],
        'Asp': ['GAT', 'GAC'],
        'Val': ['GTG', 'GTA', 'GTT', 'GTC'],
        'Ala': ['GCG', 'GCA', 'GCT', 'GCC'],
        'Arg': ['CGG', 'CGA', 'CGT', 'CGC', 'AGA', 'AGG'],
        'Ser': ['AGT', 'AGC', 'TCG', 'TCA', 'TCT', 'TCC'],
        'Lys': ['AAG', 'AAA'],
        'Asn': ['AAT', 'AAC'],
        'Met': startCodons,
        'Ile': ['ATT', 'ATC'],
        'Thr': ['ACG', 'ACA', 'ACT', 'ACC'],
        'End': stopCodons,
        'Trp': ['TGA', 'TGG'],
        'Cys': ['TGT', 'TGC'],
        'Tyr': ['TAT', 'TAC'],
        'Leu': ['TTG', 'TTA', 'CTG', 'CTA', 'CTT', 'CTC'],
        'Phe': ['TTT', 'TTC'],
        'Gln': ['CAG', 'CAA'],
        'His': ['CAT', 'CAC'],
        'Pro': ['CCG', 'CCA', 'CCT', 'CCC']
    }

    CodonsAaKeys = CodonsAa.keys()


class Effect:

    gene = None
    transcript_id = None
    strand = None
    effect = None
    prot_pos = None
    non_coding_pos = None
    prot_length = None
    length = None
    which_intron = None
    how_many_introns = None
    side = None
    dist_from_coding = None
    splice_site = None
    aa_change = None
    splice_site_context = None
    cnv_type = None
    dist_from_5utr = None


def add_effects(l):
    effect_list = []

    if len(l) == 0:
        ef = Effect()
        ef.effect = "intergenic"
        effect_list.append(ef)
        return(effect_list)

    for i in l:
        ef = Effect()
        ef.effect = i[0]
        ef.gene = i[1][0]
        ef.strand = i[2]
        ef.transcript_id = i[3]

        if ef.effect == 'no-frame-shift' or ef.effect == 'frame-shift' or ef.effect == "no-frame-shift-newStop":
            ind = i[1][1].index("/")
            ef.prot_pos = int(i[1][1][:ind])
            ef.prot_length = int(i[1][1][ind+1:])

        elif ef.effect in ['intron', 'splice-site']:
            ef.side = i[1][1]
            ef.dist_from_coding = int(i[1][2])
            ind = i[1][3].index("/")
            ef.which_intron = int(i[1][3][:ind])
            ef.how_many_introns = int(i[1][3][ind+1:])
            ind = i[1][4].index("/")
            ef.prot_pos = int(i[1][4][:ind])
            ef.prot_length = int(i[1][4][ind+1:])
            ef.length = int(i[1][5])
            if ef.effect == 'splice-site':
                ef.splice_site_context = i[1][6]
        elif ef.effect in ["5'UTR-intron", "3'UTR-intron", "non-coding-intron"]:
            ef.side = i[1][1]
            ind = i[1][3].index("/")
            ef.dist_from_coding = int(i[1][2])
            ef.which_intron = int(i[1][3][:ind])
            ef.how_many_introns = int(i[1][3][ind+1:])
            ef.length = int(i[1][5])
        elif ef.effect == "5'UTR" or ef.effect == "3'UTR":
            ef.side = ef.effect[:2]
            ef.dist_from_coding = int(i[1][2])
        elif ef.effect == "missense" or ef.effect == "synonymous" or ef.effect == "nonsense" or ef.effect == "coding_unknown":
            ind = i[1][3].index("/")
            ef.prot_pos = int(i[1][3][:ind])
            ef.prot_length = int(i[1][3][ind+1:])
            ef.aa_change = i[1][1] + "->" + i[1][2]
        elif ef.effect in [ "non-coding", "unknown", "tRNA:ANTICODON"]:
            ef.length = int(i[1][1])
        elif ef.effect == "noStart":
            ef.prot_pos = 1
            ef.prot_length = int(i[1][1])
        elif ef.effect == "noEnd":
            ef.prot_length = int(i[1][1])
            ef.prot_pos = int(i[1][1])
        elif ef.effect == "all":
            ef.cnv_type = i[2]
            ef.prot_length = i[1][1]
        elif ef.effect == "promoter":
            ef.dist_from_5utr = i[1][1]
        elif ef.effect == "CDS":
            ef.cnv_type = i[1][1]
            ef.prot_length = i[1][2]
        elif ef.effect == "no-mutation":
            pass
        else:
            print "Unrecognizable effect: " + ef.effect
            sys.exit(-6789)

        effect_list.append(ef)

    return(effect_list)





class Variant:

    chr = None
    pos = None
    pos_last = None
    ref = None
    seq = None
    type = None
    length = None


    effects = []


    def annotate(self, gm, refG, display=False, promoter_len = 0):


        #global stopCodons, CodonsAa, CodonsAaKeys


        if self.chr not in gm._utrModels.keys():

            ef =  Effect()
            if self.chr in refG.allChromosomes:
                effect_type = "intergenic"
                effect_gene = "intergenic"
                effect_details = "intergenic"
                ef.effect = "intergenic"


            else:
                effect_type = "unk_chr"
                effect_gene = "unk_chr"
                effect_details = "unk_chr"
                ef.effect = "unk_chr"

            if display == True:
                print("EffectType: " + effect_type),
                print("\tEffectGene: " + effect_gene),
                print("\tEffectDetails: " + effect_details)

            return([ef])


        if self.chr in ['MT', 'chrM', 'M']:
            code = MitochondrialCode()
            promoter_len = 0
        else:
            code = NuclearCode()


        worstForEachTranscript = []


        for key in gm._utrModels[self.chr]:
            if self.pos <= key[1] + promoter_len and self.pos_last >= key[0] - promoter_len:

                for i in gm._utrModels[self.chr][key]:

                    if self.seq == None and self.type != "deletion":
                        worstForEachTranscript.append(["unknown", [i.gene, i.CDS_len()/3], i.strand, i.trID])
                        continue

                    what_hit = i.what_region(self.chr, self.pos, self.pos_last, prom = promoter_len)
                    if what_hit == "no_hit":
                        # intergenic
                        continue

                    if what_hit == "promoter":
                        if i.strand == "+":
                            dist_from_5utr = i.exons[0].start - self.pos_last
                        else:
                            dist_from_5utr = self.pos - i.exons[-1].stop
                        worstForEachTranscript.append([what_hit, [i.gene, dist_from_5utr], i.strand, i.trID])
                        continue

                    if what_hit == "all":
                        if i.is_coding() == True:
                            transcript_length =  i.CDS_len()
                            protLength = transcript_length/3
                            worstForEachTranscript.append([what_hit, [i.gene, protLength], i.strand, i.trID])
                        else:
                            worstForEachTranscript.append(["non-coding", [i.gene, i.total_len()], i.strand, i.trID])
                        continue

                    worstEffect = None

                    if what_hit == "non-coding":
                        in_exon = False
                        all_regs = i.all_regions()
                        """
                        if all_regs == []:
                            worstForEachTranscript.append(["regulatory", [i.gene, i.total_len()], i.strand, i.trID])
                            continue
                        """
                        for r in all_regs:
                            if (r.start <= self.pos <= r.stop) or (self.pos < r.start and self.pos_last >= r.start):
                                if i.gene.startswith("tRNA"):
                                    if 'anticodonB' in i.attr:
                                        if (int(i.attr['anticodonB']) <= self.pos <= int(i.attr['anticodonE'])) or (int(i.attr['anticodonB']) > self.pos and self.pos_last >= int(i.attr['anticodonB'])):
                                            worstForEachTranscript.append(["tRNA:ANTICODON", [i.gene, i.total_len()], i.strand, i.trID])
                                            in_exon = True
                                            break

                                worstForEachTranscript.append(["non-coding", [i.gene, i.total_len()], i.strand, i.trID])
                                in_exon = True
                                break
                        if in_exon == False:
                            hit = prepareIntronHit(i, self.pos, self.length, i.all_regions())
                            worstForEachTranscript.append(["non-coding-intron", hit, i.strand, i.trID])
                        continue


                    if what_hit == "5'UTR" or what_hit == "3'UTR" :
                        if self.pos_last != self.pos:
                            if self.pos_last < i.cds[0]:
                                closestToCod = maxInExons(self.pos, self.pos_last, i.exons)
                            else:
                                closestToCod = minInExons(self.pos, self.pos_last, i.exons)

                            d = distanceFromCoding(closestToCod, i)
                        else:
                            d = distanceFromCoding(self.pos, i)
                        worstForEachTranscript.append([what_hit, [i.gene, what_hit, str(d)], i.strand, i.trID])
                        continue

                    if what_hit == "5'UTR-intron" or what_hit == "3'UTR-intron":
                        if what_hit == "5'UTR-intron":
                            if i.strand == "+":
                                regions = i.UTR5_regions()
                                if regions[-1].stop + 1 < i.cds[0]:
                                    regions.append(i.CDS_regions()[0])
                            else:
                                regions = i.UTR5_regions()
                                if regions[0].start - 1 > i.cds[1]:
                                    regions.insert(0,i.CDS_regions()[-1])
                            hit = prepareIntronHit(i, self.pos, self.length, regions)
                        else:
                            if i.strand == "-":
                                regions = i.UTR3_regions()
                                if regions[-1].stop + 1 < i.cds[0]:
                                    regions.append(i.CDS_regions()[0])
                            else:
                                regions = i.UTR3_regions()
                                if regions[0].start - 1 > i.cds[1]:
                                    regions.insert(0,i.CDS_regions()[-1])
                            hit = prepareIntronHit(i, self.pos, self.length, regions)
                        worstForEachTranscript.append([what_hit, hit, i.strand, i.trID])
                        continue

                    if self.type == "complex":
                        va = VariantAnnotator(refG, NuclearCode())
                        res = va.annotate(what_hit, i, self.chr, self.pos,
                                          self.length, self.ref, self.seq)
                        worstForEachTranscript.extend(res)

                    elif self.type == "+" or self.type == "-":

                        if what_hit == "CDS":
                            transcript_length = i.CDS_len()
                            protLength = transcript_length/3
                            worstForEachTranscript.append(["CDS",[i.gene, self.type, protLength],i.strand, i.trID])
                            continue
                        if what_hit == "intronic":
                            codingRegions = i.CDS_regions()
                            hit = prepareIntronHit(i, self.pos, self.length, codingRegions)
                            worstForEachTranscript.append(["intron", hit, i.strand, i.trID])
                            continue
                        print("Unknown cvs mutation type: " + what_hit)
                        sys.exit(-999)
                    else:
                        print("Unrecognizable mutation type: " + self.type)
                        sys.exit(-998)


        ef_list = add_effects(worstForEachTranscript)


        if display == True:
            effect_type, effect_gene, effect_details = effect_description(ef_list)
            print("EffectType: " + effect_type),
            print("\tEffectGene: " + effect_gene),
            print("\tEffectDetails: " + effect_details)

        return(ef_list)



#-----------------------------------------------------------------------------

def get_effect_types(types=True, groups=False):
    T = ['tRNA:ANTICODON',
         'splice-site',
         'frame-shift',
         'nonsense',
         'no-frame-shift-newStop',
         'noStart',
         'noEnd',
         'missense',
         'no-frame-shift',
         'CDS',
         'synonymous',
         'coding_unknown',
         "3'UTR",
         "5'UTR",
         'intron',
         'non-coding',
         "5'UTR-intron",
         "3'UTR-intron",
         "promoter",
         "non-coding-intron",
         'unknown',
         'intergenic',
         'no-mutation',
         'CNV-',
         'CNV+']

    G = ['LGDs',
         'LoF',
         'nonsynonymous',
         'coding',
         'introns',
         'UTRs',
         'CNVs'
         ]

    if types == True:
        if groups == False:
            return(T)
        A = list(G)
        A.extend(T)
        return(A)
    if groups == True:
        return(G)
    return([])

def get_effect_types_set(s):
    s = s.split(',')
    global LOF
    global nonsyn

    Groups = {
        'LGDs'          : LOF,
        'LoF'           : LOF,
        'nonsynonymous' : nonsyn,
        'introns'       : ['intron', "non-coding-intron", "5'UTR-intron", "3'UTR-intron"],
        'UTRs'          : ["3'UTR", "5'UTR", "5'UTR-intron", "3'UTR-intron"],
        'coding'        : ['splice-site', 'frame-shift', 'nonsense', 'no-frame-shift-newStop',
                            'noStart', 'noEnd', 'missense', 'no-frame-shift', 'CDS', 'synonymous' ],
        'nonsynonymous' : ['splice-site', 'frame-shift', 'nonsense', 'no-frame-shift-newStop',
                            'noStart', 'noEnd', 'missense', 'no-frame-shift', 'CDS' ],
        'CNVs'          : ['CNV+', 'CNV-']
        }
    R = []

    for i in s:
        try:
            R.extend(Groups[i])
        except:
            R.append(i)

    return set(R)

def _in_stop_codons(s, code):
    if s in code.stopCodons:
        return True
    else:
        return False

def _in_start_codons(s, code):
    if s in code.startCodons:
        return True
    else:
        return False





def annotate_variant(gm, refG, chr=None, position=None, loc=None, var=None, ref=None, alt=None, length=None, seq=None, typ=None, promoter_len=0):
    #print chr, position, loc, var, ref, alt, length, seq, typ
    v = load_variant(chr, position, loc, var, ref, alt, length, seq, typ)
    e = v.annotate(gm, refG, promoter_len)
    for effect in e:
        print("Effect", effect.gene, effect.transcript_id, effect.strand,
              effect.effect, effect.prot_pos, effect.prot_length,
              effect.aa_change)
    return (e)



"5'UTR-intron", "3'UTR-intron"
def load_variant(chr=None, position=None, loc=None, var=None, ref=None, alt=None, length=None, seq=None, typ=None):
    v = Variant()

    if chr == None:
        if loc != None:
            loc = loc.split(":")
            try:
                v.chr = loc[0]
                position = loc[1]
            except:
                print("You must specify variant location!")
                raise

        else:
            raise Exception("You must specify variant location!")

    else:
        v.chr = str(chr)
        if position == None:
            raise Exception("You must specify variant position!")


    position = str(position)
    position = position.split("-")
    v.pos = int(position[0])
    if len(position) > 1:
        v.pos_last = int(position[1])


    if var != None:
        t = var[0].upper()
        if t == "S":
            v.type = "complex"
            a = re.match('.*\((.*)->(.*)\)', var)
            v.ref = a.group(1).upper()
            v.seq = a.group(2).upper()
            v.length = len(v.seq)-len(v.ref)+1
            v.pos_last = v.pos + v.length - 1
            print("V, ", v.pos, v.pos_last)

        elif t == "D":
            v.type = "complex"
            a = re.match('.*\((.*)\)', var)
            v.ref = "A" * int(a.group(1))
            v.seq = ""
            v.length = int(a.group(1))
            v.pos_last = v.pos + v.length - 1
        elif t == "I":
            v.type = "complex"
            a = re.match('.*\((.*)\)', var)
            v.ref = ""
            v.seq = a.group(1).upper()
            v.seq = re.sub('[0-9]+', '', v.seq)
            v.length = len(v.seq)
            v.pos_last = v.pos
            v.pos = v.pos

        elif t == "C":
            if var.startswith("complex"):
                v.type = "complex"
                a = re.match('.*\((.*)->(.*)\)', var)
                v.ref = a.group(1).upper()
                v.seq = a.group(2).upper()
                v.length = len(v.seq)-len(v.ref)+1
                v.pos_last = v.pos + v.length - 1
            else:
                v.type = var[-1] # + or -
                v.length = v.pos_last - v.pos + 1
        else:
            raise Exception("Unknown variant!: " + var)

    else:
        if alt != None:
            v.type = "complex"
            v.seq = alt
            if ref != None:
                v.ref = ref.upper()
                v.length = len(v.seq)-len(v.ref)+1
            else:
                v.length = len(v.seq)
            v.pos_last = v.pos + v.length - 1


        elif typ == None:
            raise Exception("Unknown variant type!")

        else:
            t = typ[0].upper()
            if t == "S":
                v.type = "substitution"
                if seq == None:
                    raise Exception("You must specify the sequence of the variant (-q option)")
                v.seq = seq.upper()
                v.length = len(v.seq)
                v.pos_last = v.pos + v.length - 1
                if ref != None:
                    v.ref = ref.upper()
            elif t == "D":
                v.type = "deletion"
                if length == None:
                    raise Exception("You must specify the length of the variant (-l option)")
                v.length = int(length)
                v.pos_last = v.pos
            elif t == "I":
                v.type = "insertion"
                if seq == None:
                    raise Exception("You must specify the sequence of the variant (-q option)")
                v.seq = seq.upper()
                v.length = len(v.seq)
                v.pos_last = v.pos + v.length - 1
            elif t == "C":
                v.type = typ[-1] # + or -
                if length == None and v.pos_last == None:
                    raise Exception("You must specify the length of the variant (-l option)")
                if v.pos_last == None:
                    v.length = int(length)
                    v.pos_last = v.pos + v.length - 1
            else:
                raise Exception("Unrecognizable variant type!: " + typ)


    # OLD FORMAT
    if v.seq != None and ("^" in v.seq or "$" in v.seq):
        print >>sys.stderr, "Old format detected: " + v.seq
        v.seq = None


    #print(v.chr,v.pos,v.pos_last,v.ref,v.seq, v.type,v.length)

    return v


#------------------------------------------------------------------------------------------------------------------------


def getSeq(refGenome, chr, pos1, pos2=None):

    if pos2 == None:
        return(refGenome.getSequence(chr, pos1, pos1))
    return(refGenome.getSequence(chr, pos1, pos2))


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
            sys.exit(-23)
    return(reversed)

#def check_if_stop_codon



def checkProteinPosition(tm, pos, length, type, cds_reg):

    codingPos = []
    if type == "D":
        for i in xrange(0, length):
            for j in tm.exons:
                if pos + i >= j.start and pos + i <= j.stop and pos + i >= tm.cds[0] and pos + i <= tm.cds[1]:
                    codingPos.append(pos + i)
    else:
        codingPos = [pos]

    minPosCod = codingPos[0]
    maxPosCod = codingPos[-1]

    # protein length
    transcript_length = tm.CDS_len()
    protLength = transcript_length/3 - 1
    if (transcript_length%3) != 0:
        protLength += 1


    # minAA
    minAA = 0
    # cds_reg = tm.CDS_regions()

    if tm.strand == "+":
        for j in cds_reg:
            if  minPosCod >= j.start and minPosCod <= j.stop:
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

def maxInExons(pos1, pos2, exons):

     for e in exons[::-1]:
        if (pos1 >= e.start and pos1 <= e.stop) or (pos1 < e.start and pos2 >= e.start):
            if pos2 > e.stop:
                return(e.stop)
            return(pos2)
     return(None)

def minInExons(pos1, pos2, exons):

    for e in exons:
        if (pos1 >= e.start and pos1 <= e.stop) or (pos1 < e.start and pos2 >= e.start):
            if pos1 >= e.start:
                return(pos1)
            return(e.start)
    return(None)



def distanceFromCoding(pos, tm):


    dist = 0
    exons = tm.exons

    if pos < tm.cds[0]:
        k = 0
        while exons[k].start <= tm.cds[0]:
            if exons[k].stop <= pos:
                k += 1
                continue
            if tm.cds[0] <= exons[k].stop:
                if pos < exons[k].start:
                    dist += tm.cds[0] - exons[k].start
                else:
                    dist += tm.cds[0] - pos
                return(dist)

            if pos > exons[k].start:

                dist += exons[k].stop - pos
                k += 1
                continue

            dist += exons[k].stop - exons[k].start + 1
            k += 1
            continue

    elif pos > tm.cds[1]:
        k = 0

        while pos >= exons[k].start:
            if exons[k].stop <= tm.cds[1]:
                k += 1
                continue
            if tm.cds[1] >= exons[k].start:
                if pos <= exons[k].stop:
                    dist += pos - tm.cds[1]
                    return(dist)
                dist += exons[k].stop - tm.cds[1]
                k += 1
                continue

            if pos > exons[k].stop:
                dist += exons[k].stop - exons[k].start + 1
                k += 1
                continue

            dist += pos - exons[k].start
            return(dist)

    else:
        print(tm.cds[0], tm.cds[1], pos)
        print("The position must be either < cds.start or > cds.end!")
        sys.exit(-39)


def prepareIntronHit(tm, pos, length, cds_reg):


    protLength = 0
    for i in cds_reg:
        protLength += i.stop - i.start + 1
    protLength = protLength/3

    whichAA = -1

    howManyIntrons = len(cds_reg) - 1

    for i in xrange(0, howManyIntrons):

        if (pos < cds_reg[i+1].start and cds_reg[i].stop < pos) or  (pos + length - 1 < cds_reg[i+1].start and cds_reg[i].stop < pos + length - 1):
            whichAA += cds_reg[i].stop - cds_reg[i].start + 1
            intronLength = cds_reg[i+1].start - cds_reg[i].stop - 1
            if tm.strand == "+":
                whichAA = whichAA/3 + 1
                whichIntron = i + 1
                if cds_reg[i+1].start - pos - length + 1 < pos - cds_reg[i].stop:
                    indelside = "3'"
                    distance = cds_reg[i+1].start - pos - length + 1
                else:
                    indelside = "5'"
                    distance = pos - cds_reg[i].stop
            else:
                whichAA = protLength - whichAA/3
                whichIntron = howManyIntrons - i
                if cds_reg[i+1].start - pos - length + 1 < pos - cds_reg[i].stop:
                    indelside = "5'"
                    distance = cds_reg[i+1].start - pos - length + 1
                else:
                    indelside = "3'"
                    distance = pos - cds_reg[i].stop
            break
        else:
            whichAA += cds_reg[i].stop -  cds_reg[i].start + 1


    return([tm.gene, indelside, str(distance), str(whichIntron) + "/" + str(howManyIntrons),str(whichAA) + "/" + str(protLength), str(intronLength) ])



def reverseReport(string):
    string = string.upper()
    reversed = ''
    for s in string:
        if s == "A":
            reversed += "T"
        elif s == "T":
            reversed += "A"
        elif s == "G":
            reversed += "C"
        elif s == "C":
            reversed += "G"
        elif s == ":":
            reversed += ":"
        elif s == ".":
            reversed += "."
        elif s == "(":
            reversed += ")"
        elif s == ")":
            reversed += "("
        else:
            print("upps, error has occured!", string)
            sys.exit(-10)
    return(reversed)

def findSpliceBegin(pos, length, cds_reg):


    for i in xrange(0, len(cds_reg)-1):

        if (pos > cds_reg[i].stop and pos <= cds_reg[i+1].start) or (pos + length -1 > cds_reg[i].stop and pos + length - 1 <= cds_reg[i+1].start):

            if pos - cds_reg[i].stop < 3:
                spliceStart = cds_reg[i].stop + 1
            else:
                spliceStart = cds_reg[i+1].start - 2

            return(spliceStart)

    print("something wrong with splice report!!")
    sys.exit(-46)


def completeReport(type, pos, seq, length, word, strand, startRep, stopRep, spliceStart):

    if type == "S":

        if strand == "+":
            leftDot = spliceStart-startRep
            rightDot = spliceStart-startRep+2
            word = word[:leftDot] + ":" + word[leftDot:rightDot] + ":" + word[rightDot:]
            if pos < spliceStart:
                x = -1
            else:
                x = 0
            word = word[:pos-startRep+1+x] + "(" + word[pos-startRep+1+x] + "->" + seq + ")" + word[pos-startRep+2+x:]
        else:
            word = complement(word[::-1])
            leftDot = stopRep - spliceStart - 1
            rightDot = stopRep - spliceStart + 1
            word = word[:leftDot] + ":" + word[leftDot:rightDot] + ":" + word[rightDot:]
            if pos > spliceStart + 1:
                x = -1
            else:
                x = 0
            word = word[:stopRep-pos+1+x] + "(" + word[stopRep-pos+1+x] + "->" + complement(seq) + ")" + word[stopRep-pos+2+x:]

    elif type == "D":

        leftDot = spliceStart-startRep
        rightDot = spliceStart-startRep+2
        word = word[:leftDot] + ":" + word[leftDot:rightDot] + ":" + word[rightDot:]

        if pos >= spliceStart:
            x = 1
            if pos > spliceStart + 1:
                x += 1
        else:
            x = 0
        if pos + length  > spliceStart + 2:
            y = 1
        elif pos + length < spliceStart + 1:
            y = -1
        else:
            y = 0

        word = word[:pos-startRep+x] + "(" + word[pos-startRep+x : pos-startRep+length + 1 + y] + ")" + word[pos-startRep+length+ 1 + y:]

        if strand == "-":
            word = reverseReport(word[::-1])

    elif type == "I":

        leftDot = spliceStart-startRep
        rightDot = spliceStart-startRep+2
        word = word[:leftDot] + ":" + word[leftDot:rightDot] + ":" + word[rightDot:]
        if pos < spliceStart:
            x = -1
        elif pos > spliceStart + 1:
            x = 1
        else:
            x = 0

        word = word[:pos-startRep+1+x] + "(" + seq + ")" + word[pos-startRep+1+x:]
        if strand == "-":
            word = reverseReport(word[::-1])

    else:
        print("wrong mutation type: " + str(type))
        sys.exit(-1)

    return(word)



def findSpliceContext(tm, pos, length, seq, cds_reg, type, refGenome):

    spliceStart = findSpliceBegin(pos, length, cds_reg)
    refContext = getSeq(refGenome, tm.chr, pos - 6, pos + length + 5)

    if type == "D":
        seq = ""
    toSpliceReport = completeReport(type, pos, seq, length, refContext, tm.strand, pos - 6, pos + length + 5, spliceStart)
    return(toSpliceReport)

def checkIfSplice(chrom, pos, seq, length, splicePos, side, type, refGenome):


    splice_seq = getSeq(refGenome, chrom, splicePos[0], splicePos[1])
    print("checkIfSplice_old", chrom, pos, seq, length, splicePos, side,
          splice_seq)
    if type == "D":
        if side == "5'":
            # prev
            if pos < splicePos[0]:
                if (splicePos[0] - pos)%3 != 0:
                    worstEffect = "frame-shift"
                else:
                    if pos+length-1 >= splicePos[1]:
                        if getSeq(refGenome, chrom, pos+length, pos+length+1) == splice_seq:
                            worstEffect = "no-frame-shift"
                        else:
                            worstEffect = "splice-site"
                    else:
                        worstEffect = "splice-site"
            elif pos == splicePos[0]:
                if length == 1:
                     worstEffect = "splice-site"
                else:
                    if getSeq(refGenome, chrom, pos+length, pos+length+1) == splice_seq:
                        worstEffect = "intron"
                    else:
                        worstEffect = "splice-site"
            elif pos == splicePos[1]:
                if getSeq(refGenome, chrom, pos+length) == splice_seq[1]:
                    worstEffect = "intron"
                else:
                    worstEffect = "splice-site"
            else:
                print("Something's wrong in checkIfSplice")
                print(pos, splicePos)
                sys.exit(-81)


        else:
            #side = "3'"
            if pos <= splicePos[0]:
                if pos + length - 1 >= splicePos[1]:
                    if getSeq(refGenome, chrom, pos-2, pos-1) == splice_seq:
                        if pos + length - 1 > splicePos[1]:
                            if (splicePos[1] - pos + length - 1)%3 == 0:
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
                if getSeq(refGenome, chrom, pos-1, pos-1) ==  splice_seq[1]:
                    if length > 1:
                        if (length -1)%3 == 0:
                            worstEffect = "no-frame-shift"
                        else:
                            worstEffect = "frame-shift"
                    else:
                        worstEffect = "intron"
                else:
                    worstEffect = "splice-site"
            else:
                print("Something's wrong in checkIfSplice")
                print(pos, splicePos)
                sys.exit(-82)



    elif type == "I":

        if side == "5'":
            if pos == splicePos[0]:
                if length == 1:
                   worstEffect = "splice-site"
                else:
                    if seq[:2] == splice_seq:
                        worstEffect = "intron"
                    else:
                        worstEffect = "splice-site"
            elif pos == splicePos[1]:
                if seq[0] == splice_seq[1]:
                    worstEffect = "intron"
                else:
                    worstEffect = "splice-site"
            else:
                print("Something's wrong in checkIfSplice")
                print(pos, splicePos)
                sys.exit(-92)

        elif side == "3'":
            if pos == splicePos[0]:
                worstEffect = "intron"
            elif pos == splicePos[1]:
                if seq[-1] == splice_seq[0]:
                    worstEffect = "intron"
                else:
                    worstEffect = "splice-site"
            else:
                print("Something's wrong in checkIfSplice")
                print(pos, splicePos)
                sys.exit(-93)


    else:
        print("Incorrect type for checkIfSplice function: " + type)
        sys.exit(-54)



    return(worstEffect)
