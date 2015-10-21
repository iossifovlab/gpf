'''
Created on Oct 21, 2015

@author: lubo
'''
import numpy as np
import operator


def normalRefCopyNumber(location, gender):
    clnInd = location.find(":")
    chrome = location[0:clnInd]

    if chrome in ['chrX', 'X', '23', 'chr23']:
        if '-' in location:
            dshInd = location.find('-')
            pos = int(location[clnInd + 1:dshInd])
        else:
            pos = int(location[clnInd + 1:])

        # hg19 pseudo autosomes region: chrX:60001-2699520
        # and chrX:154931044-155260560
        if pos < 60001 or (pos > 2699520 and pos < 154931044) \
                or pos > 155260560:

            if gender == 'M':
                return 1
            elif gender != 'F':
                raise Exception('weird gender ' + gender)
    elif chrome in ['chrY', 'Y', '24', 'chr24']:
        if gender == 'M':
            return 1
        elif gender == 'F':
            return 0
        else:
            raise Exception('gender needed')
    return 2


def variantCount(bs, c, location=None, gender=None, denovoParent=None):
    normalRefCN = 2
    if location:
        normalRefCN = normalRefCopyNumber(location, gender)

        count = abs(bs[0, c] - normalRefCN)
        if count == 0 and bs.shape[0] > 1:
            # print("bs=%s; bs.shape[0]=%s" % (bs, bs.shape[0]))
            count = max([bs[o, c] for o in xrange(1, bs.shape[0])])
        if c != denovoParent:
            return [count]
        else:
            return [1, 1]


def isVariant(bs, c, location=None, gender=None):
    normalRefCN = 2

    if location:
        normalRefCN = normalRefCopyNumber(location, gender)

    if bs[0, c] != normalRefCN or \
            any([bs[o, c] != 0 for o in xrange(1, bs.shape[0])]):
        return True
    return False


def parseGeneEffect(effStr):
    geneEffect = []
    if effStr == "intergenic":
        return geneEffect

    # HACK!!! To rethink
    if effStr in ["CNV+", "CNV-"]:
        geneEffect.append({'sym': "", 'eff': effStr})
        return geneEffect

    for ge in effStr.split("|"):
        cs = ge.split(":")
        if len(cs) != 2:
            raise Exception(
                ge + " doesn't agree with the <sym>:<effect> format:" + effStr)
        sym, eff = cs
        geneEffect.append({'sym': sym, 'eff': eff})
    return geneEffect


def filter_gene_effect(geneEffects, effectTypes, geneSyms):
    if not effectTypes:
        return [x for x in geneEffects if x['sym'] in geneSyms]
    if not geneSyms:
        return [x for x in geneEffects if x['eff'] in effectTypes]
    return [x for x in geneEffects
            if x['eff'] in effectTypes and x['sym'] in geneSyms]


def str2Mat(matS, colSep=-1, rowSep="/", str2NumF=int):
    # print matS, colSep, rowSep, str2NumF
    if colSep == -1:
        return np.array([[str2NumF(c) for c in r]
                         for r in matS.split(rowSep)])
    return np.array([[str2NumF(v) for v in r.split(colSep)]
                     for r in matS.split(rowSep)])


def mat2Str(mat, colSep=" ", rowSep="/"):
    return rowSep.join([colSep.join([str(n) for n in mat[i, :]])
                        for i in xrange(mat.shape[0])])


class Variant:
    def __init__(self, atts, familyIdAtt="familyId", locationAtt="location",
                 variantAtt="variant", bestStAtt="bestState", bestStColSep=-1,
                 countsAtt="counts", effectGeneAtt="effectGene",
                 altFreqPrcntAtt="all.altFreq"):
        self.atts = atts

        self.familyIdAtt = familyIdAtt
        self.locationAtt = locationAtt
        self.variantAtt = variantAtt
        self.bestStAtt = bestStAtt
        self.bestStColSep = bestStColSep
        self.countsAtt = countsAtt
        self.effectGeneAtt = effectGeneAtt
        self.altFreqPrcntAtt = altFreqPrcntAtt

    @property
    def familyId(self):
        try:
            return self._familyId
        except AttributeError:
            pass
        self._familyId = str(self.atts[self.familyIdAtt])
        return self._familyId

    @property
    def studyName(self):
        return self.study.name

    @property
    def location(self):
        return self.atts[self.locationAtt]

    @property
    def variant(self):
        return self.atts[self.variantAtt]

    @property
    def bestStStr(self):
        return self.atts[self.bestStAtt]

    @property
    def bestSt(self):
        try:
            return self._bestSt
        except AttributeError:
            pass
        self._bestSt = str2Mat(self.atts[self.bestStAtt],
                               colSep=self.bestStColSep)
        return self._bestSt

    @property
    def countsStr(self):
        return self.atts[self.countsAtt]

    @property
    def counts(self):
        try:
            return self._counts
        except AttributeError:
            pass
        self._counts = str2Mat(self.atts[self.countsAtt], colSep=" ")
        return self._counts

    @property
    def geneEffect(self):
        try:
            return self._geneEffect
        except AttributeError:
            self._geneEffect = parseGeneEffect(self.atts[self.effectGeneAtt])
        return self._geneEffect

    @property
    def requestedGeneEffects(self):
        try:
            return self._requestedGeneEffect
        except AttributeError:
                self._requestedGeneEffect = self.geneEffect
        return self._requestedGeneEffect

    @property
    def altFreqPrcnt(self):
        try:
            return self._altFreqPrcnt
        except AttributeError:
                self._altFreqPrcnt = 0.0
                if self.altFreqPrcntAtt in self.atts:
                    self._altFreqPrcnt = float(self.atts[self.altFreqPrcntAtt])
        return self._altFreqPrcnt

    @property
    def memberInOrder(self):
        try:
            return self._memberInOrder
        except AttributeError:
            family = self.study.families[self.familyId]
            self._memberInOrder = family.memberInOrder
        return self._memberInOrder

    @property
    def inChS(self):
        mbrs = self.memberInOrder
        # mbrs = elf.study.families[self.familyId].memberInOrder
        bs = self.bestSt
        childStr = ''
        for c in xrange(2, len(mbrs)):
            if isVariant(bs, c, self.location, mbrs[c].gender):
                childStr += (mbrs[c].role + mbrs[c].gender)
        return childStr

    @property
    def phenoInChS(self):
        mbrs = self.memberInOrder
        # mbrs = elf.study.families[self.familyId].memberInOrder
        bs = self.bestSt
        childStr = ''
        for c in xrange(2, len(mbrs)):
            if isVariant(bs, c, self.location, mbrs[c].gender):
                childStr += (mbrs[c].role + mbrs[c].gender)
        phenotype = self.study.get_attr('study.phenotype')
        return childStr.replace('prb', phenotype)

    @property
    def fromParentS(self):
        if self.popType == "denovo":
            if 'fromParent' in self.atts:
                return self.atts['fromParent']
            else:
                return ''
        parentStr = ''
        mbrs = self.memberInOrder
        bs = self.bestSt
        for c in xrange(2):
            if isVariant(bs, c, self.location, mbrs[c].gender):
                parentStr += mbrs[c].role
        return parentStr

    @property
    def pedigree(self):
        mbrs = self.memberInOrder
        bs = self.bestSt
        denovo_parent = self.denovo_parent()
        res = [reduce(operator.add, [[m.role,
                                      m.gender],
                                     variantCount(bs, c, self.location,
                                                  m.gender, denovo_parent)])
               for (c, m) in enumerate(mbrs)]
        return res

    def denovo_parent(self):
        denovo_parent = None
        if self.popType == 'denovo':
            if 'fromParent' in self.atts:
                if self.atts['fromParent'] == 'mom':
                    denovo_parent = 0
                elif self.atts['fromParent'] == 'dad':
                    denovo_parent = 1
                else:
                    denovo_parent = None
        return denovo_parent

# FIXME:
#     def get_normal_refCN(self,c):
#         return normalRefCopyNumber(self.location,v.study.families[v.familyId]
#                                    .memberInOrder[c].gender)

    def is_variant_in_person(self, c):
        return isVariant(self.bestSt, c, self.location,
                         self.memberInOrder[c].gender)
