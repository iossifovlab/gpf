#!/bin/env python

from __future__ import print_function, unicode_literals, absolute_import

from builtins import object
from builtins import str
from future import standard_library
standard_library.install_aliases()  # noqa

from configparser import ConfigParser
import gzip
import sys
from collections import defaultdict
from GeneTerms import loadGeneTerm


class GeneInfo(object):
    pass


class Region(object):
    def len(self):
        return self.end-self.beg


class GenesMap(object):
    def __init__(self):
        self.chrs = defaultdict(list)

    def _addGeneRgn(self, g, rgn):
        self.chrs[rgn.chr].append((rgn, g))

    def _index(self):
        pass

    def getGenes(self, chr, b, e):
        if chr not in self.chrs:
            return []
        return [x[1] for x in self.chrs[chr] if x[0].beg < e and b < x[0].end]


def mergeIntervals(intsP):
    if len(intsP) < 2:
        return intsP

    ints = sorted(intsP, key=lambda x: x[0])
    r = []

    beg, end = ints[0]
    for b, e in ints:
        if b < end:
            end = max(end, e)
        else:
            r.append((beg, end))
            beg, end = b, e

    r.append((beg, end))
    return r


class GeneInfoDB(object):
    def __init__(self, confFile, wd):

        self.config = ConfigParser({
            'wd': wd,
        })

        self.config.read(confFile)
        self.geneInfoF = self.config.get('GeneInfo', 'geneInfoFile')
        # self._parseNCBIGeneInfo()
        # for fpropName in self.config.get('GeneInfo', 'fprops').split(","):
        #    self._loadGenePropertyFile(fpropName)

    @property
    def genes(self):
        try:
            return self._genes
        except AttributeError:
            pass
        self._parseNCBIGeneInfo()
        return self._genes

    @property
    def nsTokens(self):
        try:
            return self._nsTokens
        except AttributeError:
            pass
        self._parseNCBIGeneInfo()
        return self._nsTokens

    @property
    def fprops(self):
        try:
            return self._fprops
        except AttributeError:
            pass
        self._fprops = self.config.get('GeneInfo', 'fprops').split(",")
        for fpropName in self._fprops:
            self._loadGenePropertyFile(fpropName)
        return self._fprops

    @property
    def geneRgns(self):
        try:
            return self._geneRgns
        except AttributeError:
            pass
        self._loadGeneRegions()
        return self._geneRgns

    @property
    def geneRgnsMap(self):
        try:
            return self._geneRgnsMap
        except AttributeError:
            pass
        self._loadGeneRegions()
        return self._geneRgnsMap

    def getGeneTermIds(self):
        return [
            str(sn[10:]) for sn in self.config.sections()
            if sn.startswith('geneTerms.')]

    def getGeneTermAtt(self, id, attName):
        if self.config.has_option('geneTerms.' + id, attName):
            return self.config.get('geneTerms.' + id, attName)

    def getGeneTermAttList(self, id, attName):
        att = self.getGeneTermAtt(id, attName)
        if att is not None:
            return [a.strip() for a in att.split(',')]

    def getGeneTerms(self, id="main", inNS="sym"):
        fl = self.config.get('geneTerms.' + id, "file")
        gt = loadGeneTerm(fl)
        if not inNS:
            return gt
        if gt.geneNS == inNS:
            return gt
        if gt.geneNS == "id" and inNS == "sym":
            def rF(x):
                if x in self.genes:
                    return self.genes[x].sym
            gt.renameGenes("sym", rF)
        elif gt.geneNS == "sym" and inNS == "id":
            gt.renameGenes("id", lambda x: self.getCleanGeneId("sym", x))
        else:
            raise Exception(
                "Unknown name space for the " + id + " gene terms: |"
                + gt.geneNS + "|" + inNS + "|")
        return gt

    def getChromosomesFile(self):
        return self.config.get('chromosomes', 'file')

    def _loadGeneRegions(self):
        geneRegionsFile = self.config.get('GeneInfo', 'geneRgnsFile')
        f = gzip.open(geneRegionsFile)
        # h = f.readLine() ## not header???
        bf = defaultdict(lambda: defaultdict(list))

        for l in f:
            cs = l.strip().split("\t")
            if len(cs) != 11:
                raise Exception(
                    "Wrong number of columns in " + geneRegionsFile)
            gSym = cs[0]
            chr = cs[2]
            beg = int(cs[4])
            end = int(cs[5])
            if len(chr) > 5:
                continue
            bf[gSym][chr].append((beg, end))

        self._geneRgns = {}
        rawIdNS = self.nsTokens["sym"]

        self._geneRgns = defaultdict(list)
        self._geneRgnsMap = GenesMap()

        for gSymRaw, chrs in list(bf.items()):

            if gSymRaw not in rawIdNS:
                # print >>sys.stderr, "AAAA:", gSymRaw
                continue
            if len(rawIdNS[gSymRaw]) > 1:
                # print >>sys.stderr, "BBBB:", gSymRaw
                continue
            g = rawIdNS[gSymRaw][0]

            for chr in chrs:
                if chr[0:3] != "chr":
                    raise Exception('aaaaaa: ' + chr)

                for b, e in mergeIntervals(chrs[chr]):
                    r = Region()
                    r.chr = chr[3:]
                    r.beg = b
                    r.end = e
                    self._geneRgns[g].append(r)
                    self._geneRgnsMap._addGeneRgn(g, r)
        self._geneRgnsMap._index()

    def _loadGenePropertyFile(self, fpropName):
        print("loading", fpropName)
        fpropFN = self.config.get('GeneInfo', "fprop." + fpropName + ".file")
        fpropIdNS = self.config.get('GeneInfo', "fprop." + fpropName + ".idNS")
        if fpropIdNS not in self.nsTokens:
            raise Exception('Unknown fpropIdNS: ' + fpropIdNS)

        rawIdNS = self.nsTokens[fpropIdNS]
        for line in open(fpropFN, "r"):
            cs = line.strip().split("\t")
            if len(cs) != 2:
                raise Exception(
                    'Strange line in the gene property file ' + fpropFN)
            rawId, valS = cs
            val = float(valS)
            if rawId not in rawIdNS:
                continue
            if len(rawIdNS[rawId]) > 1:
                continue
            gi = rawIdNS[rawId][0]
            if fpropName in gi.fprops:
                raise Exception(
                    'The gene ' + gi.id + '( with rawId: ' + rawId +
                    ') has a repeated property ' + fpropName)
            gi.fprops[fpropName] = val

    def _parseNCBIGeneInfo(self):
        self._genes = {}
        self._nsTokens = {}
        with open(self.geneInfoF) as f:
            for line in f:
                if line[0] == "#":
                    # print "COMMENT: ", line
                    continue
                cs = line.strip().split("\t")
                if len(cs) != 15:
                    raise Exception('Unexpected line in the ' + self.geneInfoF)

                # Format: tax_id GeneID Symbol LocusTag Synonyms dbXrefs
                # chromosome map_location description
                # type_of_gene Symbol_from_nomenclature_authority
                # Full_name_from_nomenclature_authority Nomenclature_status
                # Other_designations Modification_date
                # (tab is used as a separator, pound sign - start of a comment)
                (tax_id, GeneID, Symbol, LocusTag, Synonyms, dbXrefs,
                    chromosome, map_location, description, type_of_gene,
                    Symbol_from_nomenclature_authority,
                    Full_name_from_nomenclature_authority, Nomenclature_status,
                    Other_designations, Modification_date) = cs

                gi = GeneInfo()
                gi.id = GeneID
                gi.sym = Symbol
                gi.syns = set(Synonyms.split("|"))
                gi.desc = description
                gi.fprops = {}

                if (gi.id in self._genes):
                    raise Exception(
                        'The gene ' + gi.id + ' is repeated twice in the ' +
                        self.self.geneInfoF + ' file')

                self._genes[gi.id] = gi
                self._addNSTokenToGeneInfo("id", gi.id, gi)
                self._addNSTokenToGeneInfo("sym", gi.sym, gi)
                for s in gi.syns:
                    self._addNSTokenToGeneInfo("syns", s, gi)
        print("loaded ", len(self._genes), "genes", file=sys.stderr)

    def _addNSTokenToGeneInfo(self, ns, token, gi):
        if ns not in self._nsTokens:
            self._nsTokens[ns] = {}
        tokens = self._nsTokens[ns]
        if token not in tokens:
            tokens[token] = []
        tokens[token].append(gi)

    def getCleanGeneId(self, ns, t):
        if ns not in self.nsTokens:
            return
        allTokens = self.nsTokens[ns]
        if t not in allTokens:
            return
        if len(allTokens[t]) != 1:
            return
        return allTokens[t][0].id

    def getCleanGeneIds(self, ns, *tokens):
        if ns not in self.nsTokens:
            return []

        r = []
        allTokens = self.nsTokens[ns]
        for t in tokens:
            if t not in allTokens:
                continue
            if len(allTokens[t]) != 1:
                continue
            r.append(allTokens[t][0].id)
        return r


if __name__ == "__main__":
    import os
    print("hi")
    wd = os.environ['DAE_DB_DIR']

    d = GeneInfoDB(wd + "/geneInfo.conf", wd)

    geneSyms = ["POGZ", "TP53"]
    print(d.getCleanGeneIds("sym", *geneSyms))

    print(len(d.geneRgns))
