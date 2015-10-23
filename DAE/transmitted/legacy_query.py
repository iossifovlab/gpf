'''
Created on Oct 21, 2015

@author: lubo
'''
from Variant import parseGeneEffect, filter_gene_effect, Variant
import gzip
import pysam
import copy
from transmitted.base_query import TransmissionConfig


class TransmissionLegacy(TransmissionConfig):

    @staticmethod
    def _present_in_parent_filter(present_in_parent):
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
            return lambda fromParent: ((len(fromParent) == 3 and
                                        'm' == fromParent[0]) or
                                       len(fromParent) == 6)
        if set(['father only', 'mother and father']) == pip:
            return lambda fromParent: ((len(fromParent) == 3 and
                                        'd' == fromParent[0]) or
                                       len(fromParent) == 6)
        if set(['father only', 'mother only', 'mother and father']) == \
                pip:
            return lambda fromParent: (len(fromParent) > 0)
        if set(['neither']) == pip:
            return lambda fromParent: (len(fromParent) == 0)

        return None

    def __init__(self, study, call_set=None):
        super(TransmissionLegacy, self).__init__(study, call_set)
        assert self._get_params("format") == 'legacy'

    def filter_transmitted_variants(self, f, colNms,
                                    minParentsCalled=0,
                                    maxAltFreqPrcnt=5.0,
                                    minAltFreqPrcnt=-1,
                                    variantTypes=None,
                                    effectTypes=None,
                                    ultraRareOnly=False,
                                    geneSyms=None):
        for l in f:
            # print "line:", l
            if l[0] == '#':
                continue
            vls = l.strip("\r\n").split("\t")
            # FIXME: empty strings for additional frequences:
            # 'EVS-freq', 'E65-freq'
            if len(colNms) != len(vls):
                print("colNms len: {}; variant col: {}".
                      format(len(colNms), len(vls)))
                raise Exception("Incorrect transmitted variants file: ")
            mainAtts = dict(zip(colNms, vls))

            mainAtts["location"] = mainAtts["chr"] + ":" + mainAtts["position"]

            if minParentsCalled != -1:
                parsCalled = int(mainAtts['all.nParCalled'])
                if parsCalled <= minParentsCalled:
                    continue

            if maxAltFreqPrcnt != -1 or minAltFreqPrcnt != -1:
                altPrcnt = float(mainAtts['all.altFreq'])
                if maxAltFreqPrcnt != -1 and altPrcnt > maxAltFreqPrcnt:
                    continue
                if minAltFreqPrcnt != -1 and altPrcnt < minAltFreqPrcnt:
                    continue

            ultraRare = int(mainAtts['all.nAltAlls']) == 1
            if ultraRareOnly and not ultraRare:
                continue

            geneEffect = None
            if effectTypes or geneSyms:
                geneEffect = parseGeneEffect(mainAtts['effectGene'])
                requestedGeneEffects = filter_gene_effect(geneEffect,
                                                          effectTypes,
                                                          geneSyms)
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
                                         regionS=None):

        transmittedVariantsFile = self._get_params('indexFile') + ".txt.bgz"
        print("Loading trasmitted variants from {}".
              format(transmittedVariantsFile))

        if isinstance(effectTypes, str):
            effectTypes = self.study.vdb.effectTypesSet(effectTypes)

        if isinstance(variantTypes, str):
            variantTypes = set(variantTypes.split(","))

        if not regionS and geneSyms and len(geneSyms) <= 10:
            regionS = self.study.vdb.get_gene_regions(geneSyms)

        if regionS:
            f = gzip.open(transmittedVariantsFile)
            colNms = f.readline().strip().split("\t")
            f.close()
            tbf = pysam.Tabixfile(transmittedVariantsFile)

            if isinstance(regionS, str):
                regionS = [regionS]

            for reg in regionS:
                try:
                    f = tbf.fetch(reg)
                    for v in self.filter_transmitted_variants(
                            f, colNms,
                            minParentsCalled,
                            maxAltFreqPrcnt,
                            minAltFreqPrcnt,
                            variantTypes,
                            effectTypes,
                            ultraRareOnly,
                            geneSyms):

                        yield v
                except ValueError as ex:
                    print("Bad region: {}".format(ex))
                    continue
        else:
            f = gzip.open(transmittedVariantsFile)
            colNms = f.readline().strip().split("\t")
            # print(colNms)
            for v in self.filter_transmitted_variants(f, colNms,
                                                      minParentsCalled,
                                                      maxAltFreqPrcnt,
                                                      minAltFreqPrcnt,
                                                      variantTypes,
                                                      effectTypes,
                                                      ultraRareOnly,
                                                      geneSyms):
                yield v

        if regionS:
            tbf.close()
        else:
            f.close()

    def get_transmitted_variants(self, inChild=None,
                                 presentInChild=None,
                                 gender=None,
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
                                 TMM_ALL=False):

        transmittedVariantsTOOMANYFile = \
            self._get_params('indexFile') + "-TOOMANY.txt.bgz"

        pipFilter = self._present_in_parent_filter(presentInParent)
        picFilter = self.study._present_in_child_filter(presentInChild, gender)

        if TMM_ALL:
            tbf = gzip.open(transmittedVariantsTOOMANYFile)
        else:
            tbf = pysam.Tabixfile(transmittedVariantsTOOMANYFile)

        for vs in self.get_transmitted_summary_variants(minParentsCalled,
                                                        maxAltFreqPrcnt,
                                                        minAltFreqPrcnt,
                                                        variantTypes,
                                                        effectTypes,
                                                        ultraRareOnly,
                                                        geneSyms, regionS):
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
                    for l in tbf.fetch(chrom, posI-1, posI):
                        _chrL, posL, varL, fdL = l.strip().split("\t")

                        if chrom == chrom and pos == posL and var == varL:
                            flns.append(fdL)
                    if len(flns) != 1:
                        raise Exception('TOOMANY mismatch')
                    fmsData = flns[0]

            for fmData in fmsData.split(";"):
                cs = fmData.split(":")
                if len(cs) != 3:
                    raise Exception("Wrong family data format: " + fmData)
                familyId, bestStateS, cntsS = cs
                if familyIds and familyId not in familyIds:
                    continue
                v = copy.copy(vs)
                v.atts = {kk: vv for kk, vv in vs.atts.items()}
                v.atts['familyId'] = familyId
                v.atts['bestState'] = bestStateS
                v.atts['counts'] = cntsS

                if picFilter:
                    if not picFilter(v.inChS):
                        continue
                elif inChild and inChild not in v.inChS:
                    continue
                if pipFilter:
                    if not pipFilter(v.fromParentS):
                        continue

                yield v
        tbf.close()
