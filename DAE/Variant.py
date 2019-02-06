'''
Created on Oct 21, 2015

@author: lubo
'''
from __future__ import print_function

import numpy as np
import operator
import logging

from Family import Person

LOGGER = logging.getLogger(__name__)


def chromosome_prefix(genomes_db=None):
    if genomes_db is None:
        from DAE import genomesDB
        genome = genomesDB.get_genome()  # @UndefinedVariable
    else:
        genome = genomes_db.get_genome()

    assert genome is not None
    with open(genome.genomicIndexFile) as genomic_index:
        chr_names = [ln.split("\t")[0] for ln in genomic_index]
        chr1 = chr_names[0]
        assert chr1 == "1" or chr1 == "chr1"
        if "chr" in chr1:
            return "chr"
        else:
            return ""



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
            elif gender == 'U':
                pass
                # LOGGER.debug(
                #     'unspecified gender when calculating normal number '
                #     'of allels '
                #     'in chr%s',
                #     location
                # )
                # return 1
            elif gender != 'F':
                raise Exception('weird gender ' + gender)
    elif chrome in ['chrY', 'Y', '24', 'chr24']:
        if gender == 'M':
            return 1
        elif gender == 'U':
            # LOGGER.debug(
            #     'unspecified gender when calculating normal number of '
            #     'allels '
            #     'in chr%s',
            #     location
            # )
            return 1
        elif gender == 'F':
            return 0
        else:
            raise Exception('gender needed')
    return 2


def variantCount(bs, c, location=None, gender=None, denovoParent=None):
    normal = 2
    if location:
        normal = normalRefCopyNumber(location, gender)
        # print("variantCount: {}, {}, {}".format(
        # location, gender, normalRefCN))
        ref = bs[0, c]
        # print("count: {}".format(count))
        count = 0
        if bs.shape[0] == 2:
            alles = bs[1, c]
            if alles != 0:
                if ref == normal:
                    print("location: {}, gender: {}, c: {}, normal: {}, bs: {}"
                          .format(location, gender, c, normal, bs))
                count = alles
        elif bs.shape[0] == 1:
            if normal != ref:
                count = ref

        if c != denovoParent:
            return [count]
        else:
            return [1, 'd']


def variant_count_v3(bs, c, location=None, gender=None, denovoParent=None):
    normal = 2
    if location:
        normal = normalRefCopyNumber(location, gender)
        # print("variantCount: {}, {}, {}".format(
        # location, gender, normalRefCN))
        ref = bs[0, c]
        # print("count: {}".format(count))
        count = 0
        if bs.shape[0] == 2:
            alles = bs[1, c]
            if alles != 0:
                if ref == normal:
                    print("location: {}, gender: {}, c: {}, normal: {}, bs: {}"
                          .format(location, gender, c, normal, bs))
                count = alles
        elif bs.shape[0] == 1:
            if normal != ref:
                count = ref

        if c != denovoParent:
            return [count, 0]
        else:
            return [0, 1]


def isVariant(bs, c, location=None, gender=None):
    normalRefCN = 2

    if location:
        normalRefCN = normalRefCopyNumber(location, gender)

    if bs[0, c] != normalRefCN or \
            any([bs[o, c] != 0 for o in xrange(1, bs.shape[0])]):
        return True
    return False


def variantInMembers(v):
    result = []
    for index, member in enumerate(v.memberInOrder):
        if isVariant(v.bestSt, index, v.location, member.gender):
            result.append(member.personId)
    return result


def splitGeneEffect(effStr, geneEffect=[]):
    for ge in effStr.split("|"):
        cs = ge.split(":")
        if len(cs) != 2:
            raise Exception(
                ge + " doesn't agree with the <sym>:<effect> format:" + effStr)
        sym, eff = cs
        geneEffect.append({'sym': sym, 'eff': eff, 'symu': sym.upper()})
    return geneEffect


def parseGeneEffect(effStr):
    geneEffect = []
    if effStr == "intergenic" or effStr == ':intergenic':
        return [{'eff': 'intergenic', 'sym': '', 'symu': ''}]

    # HACK!!! To rethink
    if effStr in ["CNV+", "CNV-"]:
        geneEffect.append({'sym': "", 'symu': '', 'eff': effStr})
        return geneEffect

    splitGeneEffect(effStr, geneEffect)
    return geneEffect


def filter_gene_effect(geneEffects, effectTypes, geneSyms):
    if effectTypes is None:
        return [x for x in geneEffects if x['symu'] in geneSyms]
    if geneSyms is None:
        return [x for x in geneEffects if x['eff'] in effectTypes]
    return [x for x in geneEffects
            if x['eff'] in effectTypes and x['symu'] in geneSyms]


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
                 altFreqPrcntAtt="all.altFreq", genderAtt='gender',
                 phenotypeAtt='phenotype', studyNameAtt='studyName',
                 sampleIdAtt='SampleID'):
        self.atts = atts

        self.familyIdAtt = familyIdAtt
        self.locationAtt = locationAtt
        self.variantAtt = variantAtt
        self.bestStAtt = bestStAtt
        self.bestStColSep = bestStColSep
        self.countsAtt = countsAtt
        self.effectGeneAtt = effectGeneAtt
        self.altFreqPrcntAtt = altFreqPrcntAtt
        self.genderAtt = genderAtt
        self.phenotypeAtt = phenotypeAtt
        self.studyNameAtt = studyNameAtt
        self.sampleIdAtt = sampleIdAtt

        self._family_structure = None

    def get_attr(self, attr):
        return self.atts.get(attr, None)

    @property
    def familyId(self):
        try:
            return self._familyId
        except AttributeError:
            pass
        self._familyId = self.atts.get(self.familyIdAtt,
                                       self.atts.get(self.sampleIdAtt))
        self._familyId = str(
            self._familyId) if self._familyId else self._familyId
        return self._familyId

    @property
    def studyName(self):
        return self.atts.get(self.studyNameAtt, self.study.name)

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
            if self.familyId:
                family = self.study.families[self.familyId]
                self._memberInOrder = family.memberInOrder
            else:
                person = Person(self.atts)
                person.personId = None
                person.gender = self.atts.get(self.genderAtt, 'U')
                person.role = 'sib' if self.phenotype == 'unaffected' else 'prb'
                self._memberInOrder = [person]
        return self._memberInOrder

    @property
    def family_structure(self):
        if self._family_structure is None:
            self._family_structure = "".join([
                "{}{}".format(m.role, m.gender) for m in self.memberInOrder
            ])
        return self._family_structure

    @property
    def children_in_order(self):
        return [p for p in self.memberInOrder if p.is_child]

    @property
    def inChS(self):
        childStr = ''
        for index, person in enumerate(self.memberInOrder):
            if person.is_child and \
                    isVariant(self.bestSt, index, self.location, person.gender):
                childStr += (person.role + person.gender)
        return childStr

    @property
    def phenoInChS(self):
        return self.inChS.replace('prb', self.phenotype)

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
    def phenotype(self):
        if len(self.study.phenotypes) == 1:
            return self.study.phenotypes[0]
        else:
            return self.atts.get(self.phenotypeAtt, None)

    @property
    def family_atts(self):
        return self.study.families[self.familyId].atts

    VIP_COLORS = {
        'deletion': '#e35252',
        'duplication': '#98e352',
        'triplication': '#b8008a',
        'negative': '#aaaaaa',
        'unknown': '#ffffff',
    }

    @property
    def pedigree(self):
        mbrs = self.memberInOrder
        bs = self.bestSt

        ph = self.phenotype
        colors = None
        if self.study.name[:3] == 'VIP' and \
                hasattr(self.study, 'genetic_status'):
            colors = [
                self.VIP_COLORS.get(
                    self.study.genetic_status.get(p.personId, 'unknown'),
                    '#ffffff')
                for p in mbrs]

        denovo_parent = self.denovo_parent()
        res = [reduce(operator.add, [[m.role,
                                      m.gender],
                                     variantCount(bs, c, self.location,
                                                  m.gender, denovo_parent),
                                     ])
               for (c, m) in enumerate(mbrs)]
        # res = zip(res, colors)
        # print(res)
        if colors:
            for l, c in zip(res, colors):
                l.append(c)
        res = [ph, res]
        return res

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key < other.key

    CHROMOSOMES_ORDER = dict(
        {str(x): '0' + str(x) for x in range(1, 10)}.items() +
        {str(x): str(x) for x in range(10, 23)}.items() +
        {'X': '23', 'Y': '24'}.items())

    @property
    def key(self):
        chromosome, position = self.location.split(':')
        return (self.CHROMOSOMES_ORDER.get(chromosome, '99' + chromosome),
                int(position.split('-')[0]),
                self.variant,
                self.familyId if self.familyId else '')

    def pedigree_v3(self, legend):
        def get_color(p):
            return legend.get_color(
                p.atts[legend.id] if p.role == 'prb' else 'unaffected')

        denovo_parent = self.denovo_parent()

        members = self.memberInOrder
        bs = self.bestSt

        res = []
        dad_id, mom_id = '', ''
        for index, person in enumerate(members):
            person_list = [self.familyId, person.personId,
                           person.gender, get_color(person)]
            if person.is_child:
                person_list[2:2] += [dad_id, mom_id]
            else:
                person_list[2:2] += ['', '']
                if person.role == "mom":
                    mom_id = person.personId
                elif person.role == "dad":
                    dad_id = person.personId
            res.append(person_list +
                       variant_count_v3(bs, index, self.location,
                                        person.gender, denovo_parent))
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


PRESENT_IN_CHILD_FILTER_MAPPING = {
    'affected only':
        lambda inCh, gender: len(inCh) == 4 and 'p' == inCh[0] and
    (not gender or gender == inCh[3]),
    'unaffected only':
        lambda inCh, gender: len(inCh) == 4 and 's' == inCh[0] and
    (not gender or gender == inCh[3]),
    'affected and unaffected':
        lambda inCh, gender: len(inCh) >= 8 and 'p' == inCh[0] and
    (not gender or gender == inCh[3] or gender == inCh[7]),
    'neither':
        lambda inCh, gender: len(inCh) == 0,
    'gender':
        lambda inCh, gender: gender in inCh,

    #     "autism only":
    #     lambda inCh: (len(inCh) == 4 and 'p' == inCh[0]),
    #     "affected only":
    #     lambda inCh: (len(inCh) == 4 and 'p' == inCh[0]),
    #     "unaffected only":
    #     lambda inCh: (len(inCh) == 4 and 's' == inCh[0]),
    #     "autism and unaffected":
    #     lambda inCh: (len(inCh) >= 8 and 'p' == inCh[0]),
    #     "affected and unaffected":
    #     lambda inCh: (len(inCh) >= 8 and 'p' in inCh and 's' in inCh),
    #     "neither":
    #     lambda inCh: len(inCh) == 0,
    #
    #     ("autism only", 'F'):
    #     lambda inCh: (len(inCh) == 4 and 'p' == inCh[0] and 'F' == inCh[3]),
    #     ("affected only", 'F'):
    #     lambda inCh: (len(inCh) == 4 and 'p' == inCh[0] and 'F' == inCh[3]),
    #     ("unaffected only", 'F'):
    #     lambda inCh: (len(inCh) == 4 and 's' == inCh[0] and 'F' == inCh[3]),
    #     ("autism and unaffected", 'F'):
    #     lambda inCh: (len(inCh) >= 8 and 'p' in inCh and 's' in inCh and
    #                   ('F' in inCh)),
    #     ("affected and unaffected", 'F'):
    #     lambda inCh: (len(inCh) >= 8 and 'p' in inCh and 's' in inCh and
    #                   ('F' in inCh)),
    #     ("neither", 'F'):
    #     lambda inCh: (len(inCh) == 0),
    #
    #     ("autism only", 'M'):
    #     lambda inCh: (len(inCh) == 4 and 'p' == inCh[0] and 'M' == inCh[3]),
    #     ("affected only", 'M'):
    #     lambda inCh: (len(inCh) == 4 and 'p' == inCh[0] and 'M' == inCh[3]),
    #     ("unaffected only", 'M'):
    #     lambda inCh: (len(inCh) == 4 and 's' == inCh[0] and 'M' == inCh[3]),
    #     ("autism and unaffected", 'M'):
    #     lambda inCh: (len(inCh) >= 8 and 'p' in inCh and 's' in inCh and
    #                   ('M' in inCh)),
    #     ("affected and unaffected", 'M'):
    #     lambda inCh: (len(inCh) >= 8 and 'p' in inCh and 's' in inCh and
    #                   ('M' in inCh)),
    #     ("neither", 'M'):
    #     lambda inCh: (len(inCh) == 0),
    #     'F':
    #     lambda inCh: ('F' in inCh),
    #     'M':
    #     lambda inCh: ('M' in inCh),
}


def present_in_child_filter(present_in_child=None, gender=None):
    fall = []

    if present_in_child and len(present_in_child) != 4:
        fall = [PRESENT_IN_CHILD_FILTER_MAPPING[pic]
                for pic in present_in_child]
        if gender is None:
            gender = [None]
    elif gender:
        fall = [PRESENT_IN_CHILD_FILTER_MAPPING['gender']]
    else:
        return None

    return lambda inCh: any([f(inCh, g) for f in fall for g in gender])


def present_in_parent_filter(present_in_parent):
    if present_in_parent is None:
        return None
    pip = set(present_in_parent)

    if set(['father only']) == pip:
        return lambda fromParent: (len(fromParent) == 3 and
                                   'd' == fromParent[0])
    if set(['mother only']) == pip:
        return lambda fromParent: (len(fromParent) == 3 and
                                   'm' == fromParent[0])
    if set(['mother and father']) == pip:
        return lambda fromParent: len(fromParent) == 6
    if set(['mother only', 'father only']) == pip:
        return lambda fromParent: len(fromParent) == 3
    if set(['mother only', 'mother and father']) == pip:
        return lambda fromParent: (
            (len(fromParent) == 3 and
             'm' == fromParent[0]) or
            len(fromParent) == 6)
    if set(['mother only', 'mother and father', 'neither']) == pip:
        return lambda fromParent: (
            (len(fromParent) == 3 and
             'm' == fromParent[0]) or
            len(fromParent) == 6 or
            len(fromParent) == 0)
    if set(['father only', 'mother and father']) == pip:
        return lambda fromParent: (
            (len(fromParent) == 3 and
             'd' == fromParent[0]) or
            len(fromParent) == 6)
    if set(['father only', 'mother and father', 'neither']) == pip:
        return lambda fromParent: (
            (len(fromParent) == 3 and
             'd' == fromParent[0]) or
            len(fromParent) == 6 or
            len(fromParent) == 0)
    if set(['father only', 'mother only', 'mother and father']) == \
            pip:
        return lambda fromParent: (len(fromParent) > 0)
    if set(['neither']) == pip:
        return lambda fromParent: (len(fromParent) == 0)
    return None


def denovo_present_in_parent_filter(present_in_parent):
    if present_in_parent is None:
        return None
    pip = set(present_in_parent)

    if 'neither' in pip:
        return None

    return lambda fromParent: False
