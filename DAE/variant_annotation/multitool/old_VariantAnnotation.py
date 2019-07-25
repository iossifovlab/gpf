#!/bin/env python

# October 25th 2013
# written by Ewa

import os, sys, optparse
from subprocess import call
import re
from GeneModelFiles import *
import GenomeAccess
import numpy as np



Severity = {'tRNA:ANTICODON':30, 'all':24, 'splice-site':23, 'frame-shift':22, 'nonsense':21, 'no-frame-shift-newStop':20, 'noStart':19, 'noEnd':18, 'missense':17, 'no-frame-shift':16, 'CDS':15, 'synonymous':14, 'coding_unknown':13, 'regulatory':12, "3'UTR":11, "5'UTR": 10, 'intron':9, 'non-coding':8, "5'UTR-intron": 7,"3'UTR-intron":6,  "promoter":5, "non-coding-intron":4, 'unknown':3, 'intergenic':2, 'no-mutation':1}

LOF = ['splice-site','frame-shift','nonsense','no-frame-shift-newStop']
nonsyn = ['splice-site','frame-shift','nonsense','no-frame-shift-newStop','missense','noStart', 'noEnd', 'no-frame-shift']


class NuclearCode(object):

    stopCodons = ['TAG', 'TAA', 'TGA']
    startCodons = ['ATG']

    CodonsAa = {'Gly' : ['GGG', 'GGA', 'GGT', 'GGC'],
        'Glu' : ['GAG', 'GAA'],
        'Asp' : ['GAT', 'GAC'],
        'Val' : ['GTG', 'GTA', 'GTT', 'GTC'],
        'Ala' : ['GCG', 'GCA', 'GCT', 'GCC'],
        'Arg' : ['AGG', 'AGA', 'CGG', 'CGA', 'CGT', 'CGC'],
        'Ser' : ['AGT', 'AGC', 'TCG', 'TCA', 'TCT', 'TCC'],
        'Lys' : ['AAG', 'AAA'],
        'Asn' : ['AAT', 'AAC'],
        'Met' : startCodons,
        'Ile' : ['ATA', 'ATT', 'ATC'],
        'Thr' : ['ACG', 'ACA', 'ACT', 'ACC'],
        'Trp' : ['TGG'],
        'End' : stopCodons,
        'Cys' : ['TGT', 'TGC'],
        'Tyr' : ['TAT', 'TAC'],
        'Leu' : ['TTG', 'TTA', 'CTG', 'CTA', 'CTT', 'CTC'],
        'Phe' : ['TTT', 'TTC'],
        'Gln' : ['CAG', 'CAA'],
        'His' : ['CAT', 'CAC'],
        'Pro' : ['CCG', 'CCA', 'CCT', 'CCC']}



    CodonsAaKeys = list(CodonsAa.keys())


class MitochondrialCode(object):

    stopCodons = ['TAA', 'TAG']
    startCodons = ['ATG', 'ATA']

    CodonsAa = {'Gly' : ['GGG', 'GGA', 'GGT', 'GGC'],
        'Glu' : ['GAG', 'GAA'],
        'Asp' : ['GAT', 'GAC'],
        'Val' : ['GTG', 'GTA', 'GTT', 'GTC'],
        'Ala' : ['GCG', 'GCA', 'GCT', 'GCC'],
        'Arg' : ['CGG', 'CGA', 'CGT', 'CGC', 'AGA', 'AGG'],
        'Ser' : ['AGT', 'AGC', 'TCG', 'TCA', 'TCT', 'TCC'],
        'Lys' : ['AAG', 'AAA'],
        'Asn' : ['AAT', 'AAC'],
        'Met' : startCodons,
        'Ile' : ['ATT', 'ATC'],
        'Thr' : ['ACG', 'ACA', 'ACT', 'ACC'],
        'End' : stopCodons,
        'Trp' : ['TGA', 'TGG'],
        'End' : ['TAA', 'TAG'],
        'Cys' : ['TGT', 'TGC'],
        'Tyr' : ['TAT', 'TAC'],
        'Leu' : ['TTG', 'TTA', 'CTG', 'CTA', 'CTT', 'CTC'],
        'Phe' : ['TTT', 'TTC'],
        'Gln' : ['CAG', 'CAA'],
        'His' : ['CAT', 'CAC'],
        'Pro' : ['CCG', 'CCA', 'CCT', 'CCC']}

    CodonsAaKeys = list(CodonsAa.keys())



class Effect(object):

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

    def __repr__(self):
        return "Effect gene:{} trID:{} strand:{} effect:{} " \
            "protein pos:{}/{} aa: {}".format(
                self.gene, self.transcript_id, self.strand, self.effect,
                self.prot_pos, self.prot_length, self.aa_change)


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
            print("Unrecognizable effect: " + ef.effect)
            sys.exit(-6789)

        effect_list.append(ef)

    return(effect_list)





class Variant(object):

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


        if self.chr not in list(gm._utrModels.keys()):

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
                print(("EffectType: " + effect_type), end=' ')
                print(("\tEffectGene: " + effect_gene), end=' ')
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
                        worstForEachTranscript.append(["unknown", [i.gene, i.CDS_len() // 3], i.strand, i.trID])
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
                            protLength = transcript_length // 3
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




                    exons = i.exons
                    if self.type == "deletion":

                        codingRegions = i.CDS_regions()
			## yoonha add one more condition with codingRegions where dealWithFirst and Last Codon
                        if self.pos < i.cds[0] + 3 and self.pos <= codingRegions[0].stop: #yoonha

                            h = dealWithFirstCodon_Del(i, self.pos, self.length, codingRegions, refG, code)
                            h.append(i.strand)
                            h.append(i.trID)
                            worstForEachTranscript.append(h)

                            continue

                        if self.pos > i.cds[1] - 3 and self.pos <= i.cds[1] and self.pos >= codingRegions[-1].start: #yoonha
                            h = dealWithLastCodon_Del(i, self.pos, self.length, codingRegions, refG, code)
                            h.append(i.strand)
                            h.append(i.trID)
                            worstForEachTranscript.append(h)
                            continue

                        if self.pos <= i.cds[1] - 3 and self.pos_last > i.cds[1] - 3 and self.pos_last >= codingRegions[-1].start: #yoonha
                            h = dealWithCodingAndLastCodon_Del(i, self.pos, self.length, codingRegions, refG, code)
                            h.append(i.strand)
                            h.append(i.trID)
                            worstForEachTranscript.append(h)


                        prev = codingRegions[0].stop
                        for j in codingRegions:
                            if (self.pos < j.start and self.pos > prev) or (self.pos_last < j.start and self.pos_last > prev):
                                for s in [prev + 1, prev+2, j.start-1, j.start-2]:
                                    if self.pos <= s <= self.pos_last:
                                        if s == prev + 1 or s == prev+2:
                                            splice = (prev + 1, prev + 2)
                                            side = "5'"
                                        else:
                                            splice = (j.start-2, j.start-1)
                                            side = "3'"
                                        worstEffect = checkIfSplice(self.chr, self.pos, None, self.length, splice, side, "D", refG)

                                        if worstEffect == "splice-site":
                                            hit = prepareIntronHit(i, self.pos, self.length, codingRegions)

                                            c = findSpliceContext(i, self.pos, self.length, self.seq, codingRegions, "D", refG)
                                            hit.append(c)


                                        elif worstEffect == "intron":
                                            hit = prepareIntronHit(i,self.pos, self.length, codingRegions)
                                        elif worstEffect == "frame-shift" or worstEffect == "no-frame-shift":
                                            protPos = checkProteinPosition(i, self.pos, self.length, "D", codingRegions)
                                            hit = [i.gene, protPos]
                                        else:
                                            print("No such worst effect type: " + worstEffect)
                                            sys.exit(-65)
                                        break

                                if worstEffect == None:
                                    hit = prepareIntronHit(i, self.pos, self.length, codingRegions)
                                    worstEffect = "intron"

                                worstForEachTranscript.append([worstEffect, hit, i.strand, i.trID])
                                break

                            if self.pos_last <= j.stop and self.pos >= j.start:
                                #coding
                                if self.length % 3 != 0:
                                    worstEffect = "frame-shift"
                                else:
                                    if checkForNewStop(i, self.pos, None, self.length, "D", refG, code) == False:
                                        worstEffect = "no-frame-shift"
                                    else:
                                        worstEffect = "no-frame-shift-newStop"
                                protPos = checkProteinPosition(i, self.pos, self.length, "D", codingRegions)
                                hit = [i.gene, protPos]
                                worstForEachTranscript.append([worstEffect, hit, i.strand, i.trID])
                                break

                            prev = j.stop


                    elif self.type == "insertion":


                        worstEffect = "intergenic"


                        codingRegions = i.CDS_regions()
                        if self.pos >= i.cds[0] and self.pos <= i.cds[0]+2 :
                            h = dealWithFirstCodon_Ins(i, self.pos, self.seq, self.length, codingRegions, refG, code)
                            if h == "intergenic":
                                continue
                            h.append(i.strand)
                            h.append(i.trID)
                            worstForEachTranscript.append(h)

                            continue

                        if self.pos > i.cds[1]-2 and self.pos <= i.cds[1]:
                            h = dealWithLastCodon_Ins(i, self.pos, self.seq, self.length, codingRegions, refG, code)
                            if h == "intergenic":
                                continue
                            h.append(i.strand)
                            h.append(i.trID)
                            worstForEachTranscript.append(h)
                            continue


                        prev = codingRegions[0].stop
                        for j in range(0, len(codingRegions)):
                            if self.pos < codingRegions[j].start and self.pos > prev:
                                if self.pos - prev < 3:
                                    # splice
                                    worstEffect = checkIfSplice(self.chr, self.pos, self.seq, self.length, (prev+1, prev+2), "5'", "I", refG)
                                elif codingRegions[j].start - self.pos < 2:
                                    worstEffect = checkIfSplice(self.chr, self.pos, self.seq, self.length, (codingRegions[j].start-2, codingRegions[j].start-1),"3'", "I", refG)
                                else:
                                    # intron not splice
                                    if worstEffect == "intergenic":
                                        worstEffect = "intron"

                                if worstEffect == "splice-site" or worstEffect == "intron":
                                    hit = prepareIntronHit(i, self.pos, 1, codingRegions)
                                elif worstEffect == "frame-shift" or worstEffect == "no-frame-shift":
                                    protPos = checkProteinPosition(i, self.pos, self.length, "I", codingRegions)
                                    hit = [i.gene, protPos]
                                else:
                                    print("No such worst effect type: " + worstEffect)
                                    sys.exit(-64)


                                if worstEffect == "splice-site":
                                    c = findSpliceContext(i, self.pos, self.length, self.seq, codingRegions, "I", refG)
                                    hit.append(c)

                                worstForEachTranscript.append([worstEffect, hit, i.strand, i.trID])
                                break
                            if self.pos == codingRegions[j].start:
                                if j == 0:
                                    if i.strand == "+":
                                        worstForEachTranscript.append(["5'UTR", [i.gene, "5'UTR", "1"], i.strand, i.trID])
                                    else:
                                        worstForEachTranscript.append(["3'UTR", [i.gene, "5'UTR", "1"], i.strand, i.trID])
                                else:
                                    hit = prepareIntronHit(i, self.pos-1, 1, codingRegions)
                                    worstForEachTranscript.append(["splice-site", hit, i.strand, i.trID])

                                    c = findSpliceContext(i, self.pos, self.length, self.seq, codingRegions, "I", refG)
                                    hit.append(c)

                                break

                            codingRegions = i.CDS_regions()  # yoonha moved
                            if self.pos <= codingRegions[j].stop and self.pos > codingRegions[j].start:
                                # coding
                                protPos = checkProteinPosition(i, self.pos, 1, "I", codingRegions)
                                hit = [i.gene, protPos]
                                if self.length % 3 != 0:
                                    worstForEachTranscript.append(["frame-shift", hit, i.strand, i.trID])
                                else:
                                    if checkForNewStop(i, self.pos, self.seq, self.length, "I", refG, code) == False:
                                        worstForEachTranscript.append(["no-frame-shift", hit, i.strand, i.trID])
                                    else:
                                        worstForEachTranscript.append(["no-frame-shift-newStop", hit, i.strand, i.trID])
                                break

                            prev = codingRegions[j].stop


                    elif self.type == "substitution":

                        if self.ref == None:
                            self.ref = getSeq(refG, self.chr, self.pos)

                        if self.ref == self.seq:
                            ef = Effect()
                            ef.effect = "no-mutation"

                            if display == True:
                                print(("EffectType: no-mutation"), end=' ')
                                print(("\tEffectGene: no-mutation"), end=' ')
                                print("\tEffectDetails: no-mutation")


                            return([ef])

                        if self.pos >= i.cds[0] and self.pos <= i.cds[0]+2 and self.pos <= codingRegions[0].stop: #yoonha added the last condition
                            h = dealWithFirstCodon_Snps(i, self.pos, self.seq, refG, code)
                            h.append(i.strand)
                            h.append(i.trID)
                            worstForEachTranscript.append(h)
                            continue


                        if self.pos > i.cds[1]-3 and self.pos <= i.cds[1] and self.pos >= codingRegions[-1].start: #yoonha added the last condition
                            h = dealWithLastCodon_Snps(i, self.pos, self.seq, refG, code)
                            h.append(i.strand)
                            h.append(i.trID)
                            worstForEachTranscript.append(h)
                            continue


                        #codingRegions = i.CDS_regions() ## yoonha: move above


                        prev = codingRegions[0].stop

                        for j in codingRegions:
                            if self.pos < j.start and self.pos > prev:
                                if self.pos - prev < 3 or j.start - self.pos < 3:
                                    # splice
                                    worstEffect = "splice-site"
                                else:
                                    # intron not splice
                                    worstEffect = "intron"

                                hit = prepareIntronHit(i, self.pos, 1, codingRegions)
                                if worstEffect == "splice-site":
                                    c = findSpliceContext(i, self.pos, self.length, self.seq, codingRegions, "S", refG)
                                    hit.append(c)
                                worstForEachTranscript.append([worstEffect, hit, i.strand, i.trID])

                                break

                            if self.pos <= j.stop and self.pos >= j.start:

                                # coding

                                refCodon, altCodon = whatCodonChange_Snp(i, self.pos, self.seq, refG)


                                refAA = cod2aa(refCodon, code)
                                altAA = cod2aa(altCodon, code)


                                worstEffect = mutationType(refAA, altAA)


                                protPos = checkProteinPosition(i, self.pos, 1, "S", codingRegions)

                                hit = [i.gene, refAA, altAA, protPos]

                                worstForEachTranscript.append([worstEffect, hit, i.strand, i.trID])

                                break



                            prev = j.stop


                    elif self.type == "+" or self.type == "-":

                        if what_hit == "CDS":
                            transcript_length =  i.CDS_len()
                            protLength = transcript_length // 3
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
            print(("EffectType: " + effect_type), end=' ')
            print(("\tEffectGene: " + effect_gene), end=' ')
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
    return (e)


def major_effect(E):

    global Severity

    max_effect = ""

    max = -1

    for i in E:
        if Severity[i.effect] > max:
            max = Severity[i.effect]
            max_effect = i.effect

    return(max_effect)

def with_lof(E):
    global LOF
    R = []
    for ef in E:
        if ef.effect in LOF:
            R.append(ef)
    return(R)


def longest_protein(Effects, protein_pos=False, return_ef=False):
    R = []
    max_ind = np.argmax([ef.prot_length for ef in Effects])
    e = Effects[max_ind]
    if e.prot_length == None:
        return(None)
    if return_ef == False:
        if protein_pos == True:
            return(str(e.prot_pos) + "/" + str(e.prot_length))
        return(e.prot_length)
    else:
        return(e)



def protein_position(e): ###
    if e.prot_pos == None:
        return(None)
    else:
        return(str(e.prot_pos) + "/" + str(e.prot_length))


def create_effect_details(e):

    if e.effect in ["intron", "5'UTR-intron", "3'UTR-intron", "non-coding-intron"]:
        eff_d = str(e.which_intron) + "/" + str(e.how_many_introns) + "[" + str(e.dist_from_coding) + "]"
    elif e.effect == "frame-shift" or e.effect == "no-frame-shift" or e.effect == "no-frame-shift-newStop":
        eff_d = str(e.prot_pos) + "/" + str(e.prot_length)
    elif e.effect == "splice-site" or e.effect == "synonymous":
        eff_d = str(e.prot_pos) + "/" + str(e.prot_length)
    elif e.effect == "5'UTR" or e.effect == "3'UTR":
        eff_d = str(e.dist_from_coding)
    elif e.effect in ["non-coding", "unknown", "tRNA:ANTICODON"]:
        eff_d = str(e.length)
    elif e.effect == "noStart" or e.effect == "noEnd":
        eff_d = str(e.prot_length)
    elif e.effect == "missense" or e.effect == "nonsense" or e.effect == "coding_unknown":
        eff_d = str(e.prot_pos) + "/" + str(e.prot_length) + "(" + e.aa_change + ")"
    elif e.effect == "promoter":
        eff_d = str(e.dist_from_5utr)
    elif e.effect == "CDS" or  e.effect == "all":
        eff_d = str(e.prot_length)
    elif e.effect == "no-mutation":
        eff_d = "no-mutation"
    return(eff_d)



def effect_description(E):

    global Severity

    #cnvs ???

    if E[0].effect == 'unk_chr':
        return('unk_chr', 'unk_chr', 'unk_chr')


    effect_type = ""
    effect_gene = ""
    effect_details = ""

    D = {}

    for i in E:
        severity_score = Severity[i.effect]
        try:
            D[severity_score].append(i)
        except:
            D[severity_score] = [i]

    set_worst_effect = False

    for key in sorted(D, key=int, reverse=True):

        if set_worst_effect == False:
            effect_type = D[key][0].effect
            set_worst_effect = True

        if  effect_type == "intergenic":
            return("intergenic", "intergenic", "intergenic")

        if  effect_type == "no-mutation":
            return("no-mutation","no-mutation", "no-mutation")

        G = {}
        for i in D[key]:

            try:
                G[i.gene].append(i)
            except:
                G[i.gene] = [i]

        for gene in G:
            for v in G[gene]:
                effect_details += create_effect_details(v) + ";"
            effect_gene += gene + ":" + G[gene][0].effect + "|"

        effect_details = effect_details[:-1] + "|"

    return(effect_type, effect_gene[:-1], effect_details[:-1])




def major_effect_per_gene(E):

    global Severity


    max_effect = ""

    D = {}
    for i in E:

        if i.gene in D:
            if Severity[i.effect] > D[i.gene]['max']:
                D[i.gene] = {'max':Severity[i.effect], 'ef':i.effect}
        else:
            D[i.gene] = {'max':Severity[i.effect], 'ef':i.effect}

    for key in list(D.keys()):
        max_effect += key + ":" + D[key]['ef'] + "|"


    return(max_effect[:-1])


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
            v.type = "substitution"
            a = re.match('.*\((.*)->(.*)\)', var)
            v.ref = a.group(1).upper()
            v.seq = a.group(2).upper()
            v.length = len(v.seq)-len(v.ref)+1
            v.pos_last = v.pos + v.length - 1

        elif t == "D":
            v.type = "deletion"
            a = re.match('.*\((.*)\)', var)
            v.length = int(a.group(1))
            v.pos_last = v.pos + v.length - 1
        elif t == "I":
            v.type = "insertion"
            a = re.match('.*\((.*)\)', var)
            v.seq = a.group(1).upper()
            v.seq = re.sub('[0-9]+', '', v.seq)
            v.length = len(v.seq)
            v.pos_last = v.pos

        elif t == "C":
            v.type = var[-1] # + or -
            v.length = v.pos_last - v.pos + 1

        else:
            raise Exception("Unknown variant!: " + var)

    else:
        if alt != None:
            v.type = "substitution"
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
        print("Old format detected: " + v.seq, file=sys.stderr)
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


def findFrame(tm, pos):

    if pos < tm.cds[0] or pos > tm.cds[1]:
        return(-1)


    for e in tm.exons:

        if pos >= e.start and pos <= e.stop:


            if tm.cds[0] >= e.start:
                if tm.strand == "+":
                    return((pos - tm.cds[0] + e.frame)%3)
                if tm.cds[1] <= e.stop:
                    return((tm.cds[1] - pos + e.frame)%3)
                return((e.stop - pos + e.frame)%3)
            if tm.cds[1] <= e.stop:
                if tm.strand == "+":
                    return((pos - e.start + e.frame)%3)
                return((tm.cds[1] - pos + e.frame)%3)


            if tm.strand == "+":
                return((pos - e.start + e.frame)%3)
            return((e.stop - pos + e.frame)%3)

    return(None)


def whatCodonChange_Snp(tm, pos, alt_nt, refGenome):


    frame = findFrame(tm, pos)
    orig_codon = [-1, -1, -1]

    for i in range(0, len(tm.exons)):
        if pos >= tm.exons[i].start and pos <= tm.exons[i].stop:
            orig_codon[frame] = getSeq(refGenome, tm.chr, pos)

            if tm.strand == "+":

                if frame == 0:


                    if pos+2 <= tm.exons[i].stop:
                        orig_codon[2] = getSeq(refGenome, tm.chr, pos+2)
                        orig_codon[1] = getSeq(refGenome, tm.chr, pos+1)
                    elif pos + 1 <= tm.exons[i].stop:
                        orig_codon[1] = getSeq(refGenome, tm.chr, pos+1)
                        orig_codon[2] = getSeq(refGenome, tm.chr, tm.exons[i+1].start)
                    else:
                        orig_codon[1] = getSeq(refGenome, tm.chr, tm.exons[i+1].start)
                        orig_codon[2] = getSeq(refGenome, tm.chr, tm.exons[i+1].start+1)

                elif frame == 1:

                    if pos - 1 >= tm.exons[i].start:
                        orig_codon[0] = getSeq(refGenome, tm.chr, pos-1)
                    else:
                        orig_codon[0] = getSeq(refGenome, tm.chr, tm.exons[i-1].stop)

                    if pos + 1 <= tm.exons[i].stop:
                        orig_codon[2] = getSeq(refGenome, tm.chr, pos+1)
                    else:
                        orig_codon[2] = getSeq(refGenome, tm.chr, tm.exons[i+1].start)

                elif frame == 2:
                    if pos-2 >= tm.exons[i].start:
                        orig_codon[0] = getSeq(refGenome, tm.chr, pos-2)
                        orig_codon[1] = getSeq(refGenome, tm.chr, pos-1)
                    elif pos-1 >= tm.exons[i].start:
                        orig_codon[0] = getSeq(refGenome, tm.chr, tm.exons[i-1].stop)
                        orig_codon[1] = getSeq(refGenome, tm.chr, pos-1)
                    else:
                        orig_codon[0] = getSeq(refGenome, tm.chr, tm.exons[i-1].stop-1)
                        orig_codon[1] = getSeq(refGenome, tm.chr, tm.exons[i-1].stop)

                else:
                    print(("Incorrect value of frame: " , frame))
                    sys.exit(-23)

            else:
            ## strand == "-"

                if frame == 0:
                    if pos-2 >= tm.exons[i].start:
                        orig_codon[2] = getSeq(refGenome, tm.chr, pos-2)
                        orig_codon[1] = getSeq(refGenome, tm.chr, pos-1)
                    elif pos-1 >= tm.exons[i].start:
                        orig_codon[2] = getSeq(refGenome, tm.chr, tm.exons[i-1].stop)
                        orig_codon[1] = getSeq(refGenome, tm.chr, pos-1)
                    else:
                        orig_codon[2] = getSeq(refGenome, tm.chr, tm.exons[i-1].stop-1)
                        orig_codon[1] = getSeq(refGenome, tm.chr, tm.exons[i-1].stop)


                elif frame == 1:

                    if pos - 1 >= tm.exons[i].start:
                        orig_codon[2] = getSeq(refGenome, tm.chr, pos-1)
                    else:
                        orig_codon[2] = getSeq(refGenome, tm.chr, tm.exons[i-1].stop)

                    if pos + 1 <= tm.exons[i].stop:
                        orig_codon[0] = getSeq(refGenome, tm.chr, pos+1)
                    else:
                        orig_codon[0] = getSeq(refGenome, tm.chr, tm.exons[i+1].start)

                elif frame == 2:

                    if pos+2 <= tm.exons[i].stop:
                        orig_codon[0] = getSeq(refGenome, tm.chr, pos+2)
                        orig_codon[1] = getSeq(refGenome, tm.chr, pos+1)
                    elif pos + 1 <= tm.exons[i].stop:
                        orig_codon[1] = getSeq(refGenome, tm.chr, pos+1)
                        orig_codon[0] = getSeq(refGenome, tm.chr, tm.exons[i+1].start)
                    else:
                        orig_codon[1] = getSeq(refGenome, tm.chr, tm.exons[i+1].start)
                        orig_codon[0] = getSeq(refGenome, tm.chr, tm.exons[i+1].start+1)

                else:
                    print(("Incorrect value of frame: " , frame))
                    sys.exit(-24)

    if tm.strand == "-":
        codon = complement("".join(orig_codon))
        orig_codon[frame] = alt_nt
        newCodon = complement("".join(orig_codon))
    else:
        codon = "".join(orig_codon)
        orig_codon[frame] = alt_nt
        newCodon = "".join(orig_codon)

    return(codon, newCodon)


def checkProteinPosition(tm, pos, length, type, cds_reg):

    codingPos = []
    if type == "D":
        for i in range(0, length):
            for j in tm.exons:
                if pos + i >= j.start and pos + i <= j.stop and pos + i >= tm.cds[0] and pos + i <= tm.cds[1]:
                    codingPos.append(pos + i)
    else:
        codingPos = [pos]

    minPosCod = codingPos[0]
    maxPosCod = codingPos[-1]

    # protein length
    transcript_length = tm.CDS_len()
    protLength = transcript_length // 3 - 1
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
    minAA = minAA // 3 + 1

    return(str(minAA) + "/" + str(protLength))


def mutationType(aaref, aaalt):

    if aaref == aaalt and aaref != "?":
        return("synonymous")
    if aaalt == 'End':
        return("nonsense")
    if aaref == "?" or aaalt == "?":
        return("coding_unknown")

    return("missense")


def cod2aa(codon, code):

    codon=codon.upper()
    if len(codon) != 3:
        return("?")

    for i in codon:
        if i not in ['A', 'C', 'T', 'G', 'N']:
            print("Codon can only contain: A, G, C, T, N letters, this codon is: " + codon)
            sys.exit(-21)
        if i == "N":
            return("?")

    for key in code.CodonsAaKeys:
        if codon in code.CodonsAa[key]:
            return(key)

    return(None)


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
        print((tm.cds[0], tm.cds[1], pos))
        print("The position must be either < cds.start or > cds.end!")
        sys.exit(-39)


def prepareIntronHit(tm, pos, length, cds_reg):


    protLength = 0
    for i in cds_reg:
        protLength += i.stop - i.start + 1
    protLength = protLength // 3

    whichAA = -1

    howManyIntrons = len(cds_reg) - 1

    for i in range(0, howManyIntrons):
	## yoonha: all the inequaliies below do not have "=" in original version (ewa's)
        if (pos <= cds_reg[i+1].start and cds_reg[i].stop <= pos) or  (pos + length - 1 <= cds_reg[i+1].start and cds_reg[i].stop <= pos + length - 1):
            whichAA += cds_reg[i].stop - cds_reg[i].start + 1
            intronLength = cds_reg[i+1].start - cds_reg[i].stop - 1
            if tm.strand == "+":
                whichAA = whichAA // 3 + 1
                whichIntron = i + 1
                if cds_reg[i+1].start - pos - length + 1 < pos - cds_reg[i].stop:
                    indelside = "3'"
                    distance = cds_reg[i+1].start - pos - length + 1
                else:
                    indelside = "5'"
                    distance = pos - cds_reg[i].stop
            else:
                whichAA = protLength - whichAA // 3
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
            print(("upps, error has occured!", string))
            sys.exit(-10)
    return(reversed)

def findSpliceBegin(pos, length, cds_reg):


    for i in range(0, len(cds_reg)-1):

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





def checkEndChange_Snp(codon, pos, seq, strand, code):

    if strand == "+":
        newCodon = codon[:pos] + seq + codon[pos+1:]
    else:
        newCodon = codon[:pos] + complement(seq) + codon[pos+1:]

    if not _in_stop_codons(codon, code):
    #if codon not in stopCodons:
        return('missense')
    else:
        if not _in_stop_codons(newCodon, code):
        #if newCodon not in stopCodons:
            return('noEnd')
        else:
            return('synonymous')


def firstOrLastCodonOutput_Snps(tm, pos, worstEffect):

    if worstEffect == "noEnd" or  worstEffect == "noStart":
        protLength = tm.CDS_len() // 3
        hit =[tm.gene, str(protLength)]
    elif worstEffect == "synonymous":
        p = tm.CDS_len() // 3
        hit = [tm.gene, 'End', 'End', str(p)+"/"+str(p)]
    elif worstEffect == "missense":
        p = tm.CDS_len() // 3
        hit = [tm.gene, '?', '?', str(p)+"/"+str(p)]
    else:
        print("incorrect mut type: " + worstEffect)
        sys.exit(-222)

    return([worstEffect, hit])




def dealWithFirstCodon_Snps(tm, pos, altNt, refGenome, code):

    if tm.strand == "+":
        #worstEffect = "noStart"
        if not _in_start_codons(getSeq(refGenome, tm.chr, tm.cds[0], tm.cds[0]+2), code):
            refCodon, altCodon = whatCodonChange_Snp(tm, pos, altNt, refGenome)
            refAA = cod2aa(refCodon, code)
            altAA = cod2aa(altCodon, code)
            worstEffect = mutationType(refAA, altAA)
            #worstEffect = "missense"
            p = tm.CDS_len() // 3
            hit = [tm.gene, refAA, altAA, "1/"+str(p)]
            #hit = [gene, '?', '?', pos, pos, "1/"+str(p)]
            return([worstEffect, hit])
        else:
            worstEffect = "noStart"

    else:
        worstEffect = checkEndChange_Snp(complement(getSeq(refGenome, tm.chr, tm.cds[0], tm.cds[0]+2))[::-1], abs(pos-tm.cds[0]-2), altNt, '-', code)
    out = firstOrLastCodonOutput_Snps(tm, pos, worstEffect)

    return(out)

def dealWithLastCodon_Snps(tm, pos, altNt, refGenome, code):

    if tm.strand == "+":
        worstEffect = checkEndChange_Snp(getSeq(refGenome, tm.chr, tm.cds[1]-2, tm.cds[1]), tm.cds[1]-pos, altNt, '+', code)
    else:
        if not _in_start_codons(complement(getSeq(refGenome, tm.chr, tm.cds[1]-2, tm.cds[1]))[::-1], code):
            worstEffect = "missense"
            p = tm.CDS_len() // 3
            hit = [tm.gene, '?', '?', "1/"+str(p)]
            return([worstEffect, hit])
        else:
            worstEffect = "noStart"

    out = firstOrLastCodonOutput_Snps(tm, pos, worstEffect)

    return(out)

def firstOrLastCodonOutput_Indel(tm, pos, worstEffect, type, cds_reg, length):
    if worstEffect == "no-frame-shift" or worstEffect == "frame-shift":
        protPos = checkProteinPosition(tm, pos, length, type, cds_reg)
        hit = [tm.gene, protPos]
    elif worstEffect == "noEnd" or worstEffect == "noStart":
        protLength = tm.CDS_len() // 3
        hit =[tm.gene, str(protLength)]
    elif worstEffect == "3'UTR" or worstEffect == "5'UTR":
        d = distanceFromCoding(pos, tm)
        hit = [worstEffect, [tm.gene, worstEffect, str(d)]]

    else:
        print("incorrect mut type: " + worstEffect)
        sys.exit(-233)

    return([worstEffect, hit])


def dealWithFirstCodon_Del(tm, pos, length, cds_reg, refGenome, code):


    if pos < tm.cds[0]:
        codingDelLength = length-tm.cds[0]+pos
    else:
        codingDelLength = length


    if tm.strand == "+":
        if pos >= tm.cds[0]:
            if length%3 != 0:
                worstEffect = "noStart"
            elif  not _in_start_codons(getSeq(refGenome, tm.chr, tm.cds[0], tm.cds[0]+2), code):

                worstEffect = "no-frame-shift"
            else:
                if pos == tm.cds[0]:
                    if not _in_start_codons(getSeq(refGenome, tm.chr, pos+length, pos+length+2), code):
                        worstEffect = "noStart"
                    else:
                        worstEffect = "no-frame-shift"
                else:
                    if not _in_start_codons(getSeq(refGenome, tm.chr, tm.cds[0], pos-1) + getSeq(refGenome, tm.chr, pos+length, pos+length+2)[:3], code):
                        worstEffect = "noStart"
                    else:
                        worstEffect = "no-frame-shift"
                '''
                if getSeq(refGenome, tm.chr, pos+length, pos+length+2) != "ATG"[pos-tm.cds[0]:]:
                    worstEffect = "noStart"
                else:
                    worstEffect = "no-frame-shift"
                '''
        else:
            if not _in_start_codons(getSeq(refGenome, tm.chr, tm.cds[0], tm.cds[0] +2), code):

                if (codingDelLength)%3 != 0:
                    worstEffect = "frame-shift"
                else:
                    worstEffect = "no-frame-shift"
            else:
                if codingDelLength > 3:
                    if (codingDelLength)%3 != 0:
                        worstEffect = "frame-shift"
                    else:
                        if  _in_start_codons(getSeq(refGenome, tm.chr, pos - 3, pos - 1), code):
                            worstEffect = "no-frame-shift"
                        else:
                            worstEffect = "noStart"
                else:
                    if _in_start_codons(getSeq(refGenome, tm.chr, pos - codingDelLength, pos-1) + getSeq(refGenome, tm.chr, tm.cds[0] + codingDelLength, tm.cds[0] + 2), code):

                    # if getSeq(refGenome, tm.chr, pos - codingDelLength, pos-1) == "ATG"[:codingDelLength]:
                        worstEffect = "no-frame-shift"
                    else:
                        worstEffect = "noStart"
    # strand == "-"
    else:
        lastCodon = complement(getSeq(refGenome, tm.chr, tm.cds[0], tm.cds[0] +2))[::-1]

        if not _in_stop_codons(lastCodon, code):
            if codingDelLength%3 != 0:
                worstEffect = "frame-shift"
            else:
                worstEffect = "no-frame-shift"
        else:
            if pos <= tm.cds[0]:
                if codingDelLength <= 3:

                    if _in_stop_codons(complement(getSeq(refGenome, tm.chr, tm.cds[0] + codingDelLength, tm.cds[0]+2)[::-1] + getSeq(refGenome, tm.chr,pos-codingDelLength, pos-1)[::-1]), code):

                       worstEffect = "no-frame-shift"
                    else:
                        worstEffect = "noEnd"
                else:
                    if codingDelLength%3 != 0:
                       worstEffect = "frame-shift"
                    else:
                        if _in_stop_codons(complement(getSeq(refGenome, tm.chr,pos-3, pos-1)[::-1]), code):
                            worstEffect = "no-frame-shift"
                        else:
                            worstEffect = "noEnd"

            else:
                if codingDelLength > 1:

                    x = pos - tm.cds[0] + length - 1

                    if x > 2:

                        if codingDelLength%3 == 0:
                            if _in_stop_codons(complement(getSeq(refGenome, tm.chr, pos-2, pos-1) +  getSeq(refGenome, tm.chr, tm.cds[0]+x+1))[::-1], code):
                                worstEffect = "no-frame-shift"
                            else:
                                worstEffect = "noEnd"
                        else:
                            worstEffect = "frame-shift"
                    else:
                        if x == 2:
                            if _in_stop_codons(complement(getSeq(refGenome, tm.chr, pos-3, pos-1))[::-1], code):
                                worstEffect = "no-frame-shift"
                            else:
                                worstEffect = "noEnd"
                        elif x == 1:
                            if _in_stop_codons(complement(getSeq(refGenome, tm.chr, tm.cds[0]+2) + getSeq(refGenome, tm.chr, pos-2, pos-1))[::-1], code):

                                worstEffect = "no-frame-shift"
                            else:
                                worstEffect = "noEnd"
                        else:
                            if _in_stop_codons(complement(getSeq(refGenome, tm.chr, tm.cds[0] +1, tm.cds[0] +2) + getSeq(refGenome, tm.chr, pos, pos-1))[::-1], code):

                                worstEffect = "no-frame-shift"
                            else:
                                worstEffect = "noEnd"

                else:

                    if pos == tm.cds[0] + 2:
                        worstEffect = "noEnd"
                    else:
                        if _in_stop_codons("T" + complement(getSeq(refGenome, tm.chr, tm.cds[0])) + complement(getSeq(refGenome, tm.chr, pos-2)), code):

                            worstEffect = "no-frame-shift"
                        else:
                            worstEffect = "noEnd"




    out =  firstOrLastCodonOutput_Indel(tm, pos, worstEffect, "D", cds_reg, length)
    return(out)



def dealWithLastCodon_Del(tm, pos, length, cds_reg, refGenome, code):


    dist = pos - tm.cds[1]

    if tm.strand == "+":
        if not _in_stop_codons(getSeq(refGenome, tm.chr, tm.cds[1] -2, tm.cds[1]), code):
            worstEffect = "no-frame-shift"
        else:
           if  getSeq(refGenome, tm.chr, tm.cds[1] -2, pos-1): ##
               worstEffect = "no-frame-shift"
           else:
               worstEffect = "noEnd"

    else:
        if not _in_start_codons(complement(getSeq(refGenome, tm.chr, tm.cds[1] -2, tm.cds[1]))[::-1], code):
            if pos == tm.cds[1]-2 and length >= 3:
                worstEffect = "no-frame-shift"
            else:
                worstEffect = "frame-shift"
        else:
            if _in_start_codons(complement(getSeq(refGenome, tm.chr, tm.cds[1] -2, pos-1) + getSeq(refGenome, tm.chr, pos + length, pos + length - dist))[::-1], code):
                worstEffect = "no-frame-shift"
            else:
                worstEffect = "noStart"



    out =  firstOrLastCodonOutput_Indel(tm, pos, worstEffect, "D", cds_reg, length)
    return(out)


def dealWithCodingAndLastCodon_Del(tm, pos, length, cds_reg, refGenome, code):

    d = tm.cds[1] - (pos + length - 1)

    if tm.strand == "+":
        if pos + length - 1 <= tm.cds[1]:
            if length%3 != 0:
                worstEffect = "frame-shift"
            else:
                if not _in_stop_codons(getSeq(refGenome, tm.chr, tm.cds[1] -2, tm.cds[1]), code):

                    worstEffect = "no-frame-shift"
                else:
                    worstEffect = "no-frame-shift"
        else:
            worstEffect = "noEnd"

    else:
        if pos + length - 1 > tm.cds[1]:
            length = tm.cds[1] - pos +  1
        if length % 3 != 0:
            worstEffect = "frame-shift"
        else:
            worstEffect = "noStart"

    out =  firstOrLastCodonOutput_Indel(tm, pos, worstEffect, "D", cds_reg, length)
    return(out)


def dealWithFirstCodon_Ins(tm, pos, seq, length, cds_reg, refGenome, code):


    if tm.strand == "+":
        if pos == tm.cds[0]:
            if tm.cds[0] == tm.tx[0]:
                return(["5'UTR", [tm.gene,"5'UTR", "1"]])
            else:
                return("intergenic")
        elif length == 1:
            if pos == tm.cds[0] + 1 and seq == "A":
                if tm.cds[0] == tm.tx[0]:
                    return(["5'UTR", [tm.gene,"5'UTR", "1"]])
                else:
                    return("intergenic")
            else:
                worstEffect = "frame-shift"

        elif not _in_start_codons(getSeq(refGenome, tm.chr, tm.cds[0], tm.cds[0]+2), code):

            if length%3 != 0:
                worstEffect = "frame-shift"
            else:
                worstEffect = "no-frame-shift"
        else:
            d = pos - tm.cds[0]
            if seq[-d:] == "AT"[:d]:
                if tm.cds[0] == tm.tx[0]:
                    return(["5'UTR", [tm.gene,"5'UTR", "1"]])
                else:
                    return("intergenic")
            elif seq[:3-d] == "TG"[:3-d]:
                if length%3 == 0:
                    worstEffect = "no-frame-shift"
                else:
                    worstEffect = "frame-shift"
            else:
                worstEffect = "noStart"
    # strand == "-"
    else:
        if pos == tm.cds[0]:
            if tm.cds[0] == tm.tx[0]:
                return(["3'UTR", [tm.gene,"3'UTR", "1"]])
            else:
                return("intergenic")
        elif not _in_stop_codons(complement(getSeq(refGenome, tm.chr, tm.cds[0],  tm.cds[0]+2))[::-1], code):

            if length%3 != 0:
                worstEffect = "frame-shift"
            else:
                worstEffect = "no-frame-shift"
        else:
            if pos - tm.cds[0] == 2:
                if length == 1:
                    if _in_stop_codons(complement(getSeq(refGenome, tm.chr, tm.cds[0]+1) + seq +getSeq(refGenome, tm.chr, tm.cds[0]+2) )[::-1], code):
                        if tm.cds[0] == tm.tx[0]:
                            return(["3'UTR", [tm.gene,"3'UTR", "1"]])
                        else:
                            return("intergenic")
                    else:
                        worstEffect = "noEnd"
                elif complement(seq[-2:])[::-1] in ['GA', 'AA', 'AG']:
                    if tm.cds[0] == tm.tx[0]:
                        return(["3'UTR", [tm.gene,"3'UTR", "1"]])
                    else:
                        return("intergenic")

                elif seq[0] == "A":
                    if length%3 == 0:
                        worstEffect = "no-frame-shift"
                    else:
                        worstEffect = "frame-shift"
                else:
                    worstEffect = "noEnd"
            elif pos - tm.cds[0] == 1:
                if _in_stop_codons(complement(seq[-1] + getSeq(refGenome, tm.chr, tm.cds[0]+1, tm.cds[0]+2))[::-1], code):
                    if tm.cds[0] == tm.tx[0]:
                        return(["3'UTR", [tm.gene,"3'UTR", "1"]])
                    else:
                        return("intergenic")
                elif length == 1:
                    worstEffect = "noEnd"
                elif _in_stop_codons(complement(getSeq(refGenome, tm.chr, tm.cds[0]) + seq[:2])[::-1], code):

                    if length%3 == 0:
                        worstEffect = "no-frame-shift"
                    else:
                        worstEffect = "frame-shift"
                else:
                    worstEffect = "noEnd"
            else:
                print("error in dealWithFirstCodon_Ins, posCod: " + str(tm.cds[0]) + " Inspos: " + str(pos))



    out =  firstOrLastCodonOutput_Indel(tm, pos, worstEffect, "I", cds_reg, length)
    return(out)


def dealWithLastCodon_Ins(tm, pos, seq, length, cds_reg, refGenome, code):

    if tm.strand == "-":
        if getSeq(refGenome, tm.chr, tm.cds[1]-2, tm.cds[1]) != "CAT":

            if length%3 == 0:
                worstEffect = "no-frame-shift"
            else:
                worstEffect = "frame-shift"
        else:
            if length == 1:
                if pos == tm.cds[1] and seq == "T":
                    if tm.cds[1] == tm.tx[1]:
                        return(["5'UTR", [tm.gene,"5'UTR", "1"]])
                    else:
                        return("intergenic")
                else:
                    worstEffect = "frame-shift"
            else:
                if pos == tm.cds[1] - 2:
                    if length%3 == 0:
                        worstEffect = "no-frame-shift"
                    else:
                        worstEffect = "frame-shift"
                else:
                    if tm.cds[1] - pos == 0:
                        if seq[0] == "T":
                            if tm.cds[1] == tm.tx[1]:
                                return(["5'UTR", [tm.gene,"5'UTR", "1"]])
                            else:
                                return("intergenic")

                        elif seq[-2:] == "CA":
                            if length%3 == 0:
                                worstEffect = "no-frame-shift"
                            else:
                                worstEffect = "frame-shift"
                        else:
                            worstEffect = "noStart"
                    elif tm.cds[1] - pos == 1:
                        if seq[:2] == "AT":
                            if tm.cds[1] == tm.tx[1]:
                                return(["5'UTR", [tm.gene,"5'UTR", "1"]])
                            else:
                                return("intergenic")
                        elif seq[-1] == "C":
                            if length%3 == 0:
                                worstEffect = "no-frame-shift"
                            else:
                                worstEffect = "frame-shift"
                        else:
                            worstEffect = "noStart"

                    else:
                        print("Error in dealWithLastCodon_Ins, pos: " + str(pos))

    # strand == "+"
    else:
        if not _in_stop_codons(getSeq(refGenome, tm.chr, tm.cds[1]-2, tm.cds[1]), code):

            if length%3 == 0:
                worstEffect = "no-frame-shift"
            else:
                worstEffect = "frame-shift"
        else:
            if pos == tm.cds[1] - 2:
                if length%3 == 0:
                    worstEffect = "no-frame-shift"
                else:
                    worstEffect = "frame-shift"
            elif length == 1:
                if pos == tm.cds[1] - 1:
                    if _in_stop_codons("T" + seq + getSeq(refGenome, tm.chr, tm.cds[1] -1), code):
                        if tm.cds[1] == tm.tx[1]:
                            return(["3'UTR", [tm.gene,"3'UTR", "1"]])
                        else:
                            return("intergenic")
                    else:
                        worstEffect = "noEnd"
                else:
                    if _in_stop_codons(getSeq(refGenome, tm.chr, tm.cds[1]-2, tm.cds[1]-1) + seq, code):
                        if tm.cds[1] == tm.tx[1]:
                            return(["3'UTR", [tm.gene,"3'UTR", "1"]])
                        else:
                            return("intergenic")
                    else:
                        worstEffect = "noEnd"
            else:
                 if pos == tm.cds[1] - 1:
                     if _in_stop_codons("T" + seq[:2], code):
                         if tm.cds[1] == tm.tx[1]:
                             return(["3'UTR", [tm.gene,"3'UTR", "1"]])
                         else:
                             return("intergenic")
                     elif seq[-1] == "T":
                         if length%3 == 0:
                             worstEffect = "no-frame-shift"
                         else:
                             worstEffect = "frame-shift"
                     else:
                         worstEffect = "noEnd"
                 else:
                     if _in_stop_codons(getSeq(refGenome, tm.chr, tm.cds[1]-2, tm.cds[1]-1) + seq[0], code):
                         if tm.cds[1] == tm.tx[1]:
                             return(["3'UTR", [tm.gene,"3'UTR", "1"]])
                         else:
                             return("intergenic")
                     elif _in_stop_codons('T' + seq[-2:], code):
                         if length%3 == 0:
                             worstEffect = "no-frame-shift"
                         else:
                             worstEffect = "frame-shift"
                     else:
                         worstEffect = "noEnd"

    out =  firstOrLastCodonOutput_Indel(tm, pos, worstEffect,"I", cds_reg, length)
    return(out)

def findCodingBase(tm, pos, dist, refGenome):

    if dist == 0:
        return(getSeq(refGenome, tm.chr, pos))

    for e in range(0, len(tm.exons)):
        if pos >= tm.exons[e].start and pos <= tm.exons[e].stop:
            if pos+dist >= tm.exons[e].start and pos+dist <= tm.exons[e].stop:
                return(getSeq(refGenome, tm.chr, pos + dist))
            if dist < 0:
                d = pos - tm.exons[e].start + dist + 1
                try:
                    return(findCodingBase(tm, tm.exons[e-1].stop, d, refGenome))
                except:
                    return("NA")
            else:
                d = tm.exons[e].stop - pos + dist - 1
                try:
                    return(findCodingBase(tm, tm.exons[e+1].start, d, refGenome))
                except:
                    return("NA")
    return(None)




def checkForNewStop_Del(pos, length, tm, refGenome, code):

    if tm.strand == "+":
        frame = findFrame(tm, pos)
        if frame == 0:
            return(False)
        if frame == 1:
            codon = findCodingBase(tm, pos,-1, refGenome ) +  findCodingBase(tm, pos, length, refGenome ) +  findCodingBase(tm, pos, length+1, refGenome )
        else:
            codon = findCodingBase(tm, pos, -2 , refGenome) +  findCodingBase(tm, pos, -1 , refGenome) + findCodingBase(tm, pos, length , refGenome)
    else:
        frame = findFrame(tm, pos + length - 1)
        if frame == 0:
            return(False)
        if frame == 1:
            codon = complement(findCodingBase(tm, pos, length , refGenome) + findCodingBase(tm, pos, -1, refGenome ) + findCodingBase(tm, pos, -2, refGenome ))
        else:
            codon = complement(findCodingBase(tm, pos, length+1 , refGenome) + findCodingBase(tm, pos, length , refGenome) + findCodingBase(tm, pos, -1, refGenome ))

    if _in_stop_codons(codon, code):
        return(True)
    return(False)

def checkForNewStop_Ins(pos, seq, tm, length, refGenome, code):



    if tm.strand == "+":
        frame = findFrame(tm, pos)
        if frame == 0:
            return(False)
        if frame == 1:
            preCodon = findCodingBase(tm, pos, -1, refGenome  ) +  seq[:2]
            postCodon = seq[-1] + findCodingBase(tm, pos, 0 , refGenome ) + findCodingBase(tm, pos, 1, refGenome  )
            if length > 3:
                for i in range(0, length // 3 - 1):
                    if _in_stop_codons(seq[i*3 + 2: i*3 + 5], code):
                        return(True)
        else:
            preCodon = findCodingBase(tm, pos, -2 , refGenome ) + findCodingBase(tm, pos, -1 , refGenome ) + seq[0]
            postCodon = seq[-2:] + findCodingBase(tm, pos, 0 , refGenome )
            if length > 3:
                for i in range(0, length // 3 - 1):
                    if _in_stop_codons(seq[i*3 + 1: i*3 + 4], code):
                        return(True)

    else:
        frame = findFrame(tm, pos)
        if frame == 2:
            return(False)
        if frame == 0:
            preCodon = complement(findCodingBase(tm, pos, 0, refGenome  ) + seq[:-3:-1])
            postCodon = complement(seq[0] + findCodingBase(tm, pos, -1 , refGenome ) + findCodingBase(tm, pos, -2 , refGenome ))

            if length > 3:
                for i in range(0, length // 3 - 1):
                    if _in_stop_codons(complement(seq[i*3+1:i*3+4])[::-1], code):
                        return(True)
        else:
            preCodon = complement(findCodingBase(tm, pos, 1 , refGenome ) + findCodingBase(tm, pos, 0 , refGenome ) + seq[-1])
            postCodon = complement(seq[1::-1] + findCodingBase(tm, pos, -1 , refGenome ))
            if length > 3:
                for i in range(0, length // 3 - 1):
                    if _in_stop_codons(complement(seq[i*3+2:i*3+5])[::-1], code):
                        return(True)

    if _in_stop_codons(preCodon, code) or _in_stop_codons(postCodon, code):
        return(True)
    return(False)

def checkForNewStop(tm, pos, seq, length, type , refGenome, code):

    if type == "D":
        return(checkForNewStop_Del(pos, length, tm, refGenome, code ))
    if type == "I":
        return(checkForNewStop_Ins(pos, seq, tm, length , refGenome, code))
    print("Incorrect type for checking new stops: " + type)
    sys.exit(-54)


def checkIfSplice(chrom, pos, seq, length, splicePos, side, type, refGenome):


    splice_seq = getSeq(refGenome, chrom, splicePos[0], splicePos[1])

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
                print((pos, splicePos))
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
                print((pos, splicePos))
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
                print((pos, splicePos))
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
                print((pos, splicePos))
                sys.exit(-93)


    else:
        print("Incorrect type for checkIfSplice function: " + type)
        sys.exit(-54)



    return(worstEffect)
