'''
Created on Oct 21, 2015

@author: lubo
'''
from __future__ import unicode_literals
from builtins import zip
from Variant import parseGeneEffect, filter_gene_effect, Variant,\
    present_in_parent_filter, present_in_child_filter, \
    filter_by_status, chromosome_prefix
import gzip
import pysam
import copy
from transmitted.base_query import TransmissionConfig
from collections import Counter
import logging

LOGGER = logging.getLogger(__name__)


class TransmissionLegacy(TransmissionConfig):

    def __init__(self, study, call_set=None):
        super(TransmissionLegacy, self).__init__(study, call_set)
        assert self._get_params("format") == 'legacy' or \
            self._get_params('indexFile') is not None

        self.CHROMOSOME_PREFIX = chromosome_prefix()

    def genomic_scores_filter(self, atts, genomicScores):
        try:
            return all([sc['min'] <= float(atts[sc['metric']]) < sc['max']
                        for sc in genomicScores])
        except ValueError:
            return False
        except KeyError:
            return False
        return False

    def filter_transmitted_variants(self, f, colNms,
                                    minParentsCalled=0,
                                    maxAltFreqPrcnt=5.0,
                                    minAltFreqPrcnt=-1,
                                    variantTypes=None,
                                    effectTypes=None,
                                    ultraRareOnly=False,
                                    geneSyms=None,
                                    genomicScores=[]):
        if maxAltFreqPrcnt is None:
            maxAltFreqPrcnt = -1
        if minAltFreqPrcnt is None:
            minAltFreqPrcnt = -1

        geneSymsUpper = None
        if geneSyms:
            geneSymsUpper = [sym.upper() for sym in geneSyms]
        for l in f:
            # print "line:", l
            if l[0] == '#':
                continue
            vls = l.strip("\r\n").split("\t")
            # FIXME: empty strings for additional frequences:
            # 'EVS-freq', 'E65-freq'
            if len(colNms) != len(vls):
                LOGGER.error("colNms len: {}; variant col: {}".
                             format(len(colNms), len(vls)))
                raise Exception("Incorrect transmitted variants file: ")
            mainAtts = dict(list(zip(colNms, vls)))
            mainAtts["location"] = mainAtts["chr"] + ":" + mainAtts["position"]

            if minParentsCalled != -1:
                parsCalled = int(mainAtts['all.nParCalled'])
                if parsCalled <= minParentsCalled:
                    continue

            if maxAltFreqPrcnt != -1 or minAltFreqPrcnt != -1:
                altPrcnt = float(mainAtts['all.altFreq'])
                if maxAltFreqPrcnt != -1 and altPrcnt >= maxAltFreqPrcnt:
                    continue
                if minAltFreqPrcnt != -1 and altPrcnt <= minAltFreqPrcnt:
                    continue

            try:
                ultraRare = int(mainAtts['all.nAltAlls']) == 1
            except ValueError:
                if ultraRareOnly:
                    raise Exception('ValueError with option "ultraRareOnly"')
                ultraRare = False

            if ultraRareOnly:
                if not ultraRare:
                    continue

            if not self.genomic_scores_filter(mainAtts, genomicScores):
                continue

            geneEffect = None
            if effectTypes or geneSymsUpper:
                geneEffect = parseGeneEffect(mainAtts['effectGene'])
                requestedGeneEffects = filter_gene_effect(geneEffect,
                                                          effectTypes,
                                                          geneSymsUpper)
                if not requestedGeneEffects:
                    continue

            v = Variant(mainAtts)
            v.study = self.study

            if geneEffect:
                v._geneEffect = geneEffect
                v._requestedGeneEffect = requestedGeneEffects
            if ultraRare:
                v.popType = "ultraRare"
            else:
                # rethink
                v.popType = "common"

            if variantTypes and v.variant[0:3] not in variantTypes:
                continue
            yield v

    def get_transmitted_summary_variants(self, minParentsCalled=0,
                                         maxAltFreqPrcnt=5.0,
                                         minAltFreqPrcnt=-1,
                                         variantTypes=None, effectTypes=None,
                                         ultraRareOnly=False, geneSyms=None,
                                         regionS=None,
                                         limit=None,
                                         genomicScores=[]):
        transmittedVariantsFile = self._get_params('indexFile') + ".txt.bgz"
        LOGGER.info("Loading trasmitted variants from {}".
                    format(transmittedVariantsFile))

        if isinstance(effectTypes, str):
            effectTypes = self.study.vdb.effectTypesSet(effectTypes)

        if isinstance(variantTypes, str):
            variantTypes = set(variantTypes.split(","))

        if not regionS and geneSyms and len(geneSyms) <= 10:
            regionS = self.study.vdb.get_gene_regions(geneSyms)

        if regionS:
            f = gzip.open(transmittedVariantsFile, mode="rt")
            colNms = f.readline().strip().split("\t")
            colNms = [cn.strip("#") for cn in colNms]
            f.close()
            tbf = pysam.Tabixfile(transmittedVariantsFile)

            if isinstance(regionS, str):
                regionS = [regionS]

            for reg in regionS:
                try:
                    if self.CHROMOSOME_PREFIX not in reg:
                        reg = self.CHROMOSOME_PREFIX + reg
                    reg = reg.encode("utf8")
                    f = tbf.fetch(reg)
                    for v in self.filter_transmitted_variants(
                            f, colNms,
                            minParentsCalled,
                            maxAltFreqPrcnt,
                            minAltFreqPrcnt,
                            variantTypes,
                            effectTypes,
                            ultraRareOnly,
                            geneSyms, genomicScores):

                        yield v
                except ValueError as ex:
                    LOGGER.warn("Bad region: {}".format(ex))
                    continue
        else:
            f = gzip.open(transmittedVariantsFile, mode="rt")

            colNms = f.readline().strip().split("\t")
            colNms = [cn.strip("#") for cn in colNms]
            for v in self.filter_transmitted_variants(
                    f, colNms,
                    minParentsCalled,
                    maxAltFreqPrcnt,
                    minAltFreqPrcnt,
                    variantTypes,
                    effectTypes,
                    ultraRareOnly,
                    geneSyms, genomicScores):
                yield v

        if regionS:
            tbf.close()
        else:
            f.close()

    def get_transmitted_variants(
            self, inChild=None,
            presentInChild=None,
            gender=None,
            roles=None,
            presentInParent=None,
            minParentsCalled=0,
            maxAltFreqPrcnt=5.0,
            minAltFreqPrcnt=-1,
            variantTypes=None,
            effectTypes=None,
            ultraRareOnly=False,
            geneSyms=None,
            familyIds=None,
            regionS=None,
            status=None,
            TMM_ALL=False,
            limit=None,
            genomicScores=[]):
        if limit is None:
            limit = 0

        query = {
            'study': self.study.name,
            'inChild': inChild,
            'presentInChild': presentInChild,
            'gender': gender,
            'roles': roles,
            'presentInParent': presentInParent,
            'minParentsCalled': minParentsCalled,
            'maxAltFreqPrcnt': maxAltFreqPrcnt,
            'minAltFreqPrcnt': minAltFreqPrcnt,
            'ultraRareOnly': ultraRareOnly,
            'variantTypes': variantTypes,
            'effectTypes': effectTypes,
            'geneSyms': geneSyms,
            'familyIds': familyIds,
            'regionS': regionS,
            'TMM_ALL': TMM_ALL,
            'limit': limit
        }

        transmittedVariantsTOOMANYFile = \
            self._get_params('indexFile') + "-TOOMANY.txt.bgz"

        pipFilter = present_in_parent_filter(presentInParent)
        picFilter = present_in_child_filter(presentInChild, gender)

        if TMM_ALL:
            tbf = gzip.open(transmittedVariantsTOOMANYFile)
        else:
            tbf = pysam.Tabixfile(transmittedVariantsTOOMANYFile)

        for vs in self.get_transmitted_summary_variants(
                minParentsCalled, maxAltFreqPrcnt, minAltFreqPrcnt,
                variantTypes, effectTypes, ultraRareOnly, geneSyms, regionS,
                genomicScores=genomicScores):
            if not vs:
                continue

            fmsData = vs.atts['familyData']
            if not fmsData:
                continue
            if fmsData == "TOOMANY":
                chrom = vs.atts['chr']
                pos = vs.atts['position']
                var = vs.atts['variant']
                if TMM_ALL:
                    for l in tbf:
                        _chrL, posL, varL, fdL = l.strip().split("\t")
                        if chrom == chrom and pos == posL and var == varL:
                            fmsData = fdL
                            break
                    if fmsData == "TOOMANY":
                        raise Exception('TOOMANY mismatch TMM_ALL')
                else:
                    flns = []
                    posI = int(pos)
                    for l in tbf.fetch(chrom, posI - 1, posI):
                        _chrL, posL, varL, fdL = l.strip().split("\t")

                        if chrom == chrom and pos == posL and var == varL:
                            flns.append(fdL)
                    if len(flns) != 1:
                        LOGGER.error(
                            "Error: chrome: {}, posI: {}, flns: {}".format(
                                chrom, posI, flns))
                        raise Exception('TOOMANY mismatch')
                    fmsData = flns[0]

            for fmData in fmsData.split(";"):
                cs = fmData.split(":")
                if len(cs) < 3:
                    raise Exception("Wrong family data format: " + fmData)
                familyId, bestStateS, cntsS = cs[:3]
                if familyIds and familyId not in familyIds:
                    continue
                v = copy.copy(vs)
                v.atts = {kk: vv for kk, vv in list(vs.atts.items())}
                v.atts['familyId'] = familyId
                v.atts['bestState'] = bestStateS
                v.atts['counts'] = cntsS

                if roles:
                    roles_in_order = [m.role for m in v.memberInOrder]
                    if not any(role in roles and v.bestSt[1][i] > 0
                               for i, role in enumerate(roles_in_order)):
                        continue
                if status:
                    if filter_by_status(v, status):
                            continue
                if picFilter:
                    if not picFilter(v.inChS):
                        continue
                elif inChild and inChild not in v.inChS:
                    continue
                if pipFilter:
                    if not pipFilter(v.fromParentS):
                        continue
                yield v

                limit -= 1
                if limit == 0:
                    raise StopIteration

        tbf.close()

    def get_families_with_transmitted_variants(self, **kwargs):
        vs = self.get_transmitted_variants(**kwargs)
        variants = []
        seen = set()
        for v in vs:
            vKs = {v.familyId + "." + ge['sym']
                   for ge in v.requestedGeneEffects}
            if seen & vKs:
                continue
            variants.append(v)
            seen |= vKs

        families = Counter([v.familyId for v in variants])
        return families
