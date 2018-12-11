#!/usr/bin/env python
from __future__ import print_function

import os
import sys

from box import Box

from annotation.tools.annotator_base import VariantAnnotatorBase
from annotation.tools import score_file_io
from annotation.tools.schema import Schema

# chrInd = {}
# # faiFN="/data/unsafe/autism/genomes/GATK_ResourceBundle_5777_b37_phiX174/
#       chrAll.fa.fai"
# faiFN = genomesDB.get_genome().genomicIndexFile
# FAIF = open(faiFN)
# chrName = [ln.split("\t")[0] for ln in FAIF]
# FAIF.close()
# chrInd = {chN: chI for chI, chN in enumerate(chrName)}


class FrequencyAnnotator(VariantAnnotatorBase):

    def __init__(self, config):
        super(FrequencyAnnotator, self).__init__(config)

        self._init_freq_file()

        assert len(self.config.native_columns) >= 1
        self.score_names = self.config.native_columns
        self.freq_column = self.config.options.freq
        self.freq_output = self.config.columns_config['freq']
        assert self.freq_column in self.freq_file.header, \
            "{} not in {}".format(self.freq_column, self.freq_file.header)
        assert 'variant' in self.freq_file.header, \
            "'variant' not in {}".format(self.freq_file.header)

    def _init_freq_file(self):
        if not self.config.options.freq_file:
            print("You should provide a freq file location.", file=sys.stderr)
            sys.exit(1)

        freq_filename = os.path.abspath(self.config.options.freq_file)
        if not os.path.exists(freq_filename):
            wd = os.environ.get("DAE_DB_DIR", ".")
            freq_filename = os.path.join(wd, self.config.options.freq_file)
            freq_filename = os.path.abspath(freq_filename)
        assert os.path.exists(freq_filename), freq_filename

        assert self.config.options.freq is not None

        score_config = Box({
                "columns": {
                    "chr": "chr",
                    "pos_begin": "position",
                    "score": self.config.options.freq,
                },
                "schema": Schema.from_dict({
                    "str": "chr,variant",
                    "int": "position",
                    "float": "freq",
                })
            },
            default_box=True,
            default_box_attr=None)

        if self.config.options.direct:
            self.freq_file = score_file_io.DirectAccess(
                self.config.options,
                freq_filename,
                config_filename=None,
                score_config=score_config)
        else:
            self.freq_file = score_file_io.IterativeAccess(
                self.config.options,
                freq_filename,
                config_filename=None,
                score_config=score_config)
        self.freq_file._setup()

        self.no_score_value = None

    def collect_annotator_schema(self, schema):
        super(FrequencyAnnotator, self).collect_annotator_schema(schema)
        for native, output in self.config.columns_config.items():
            schema.columns[output] = \
                self.freq_file.schema.columns[native]

    def _freq_not_found(self, aline):
        aline[self.freq_output] = self.no_score_value

    def do_annotate(self, aline, variant):
        if variant is None:
            self._freq_not_found(aline)
            return
        chrom = variant.chromosome
        pos = variant.details.cshl_position

        scores = self.freq_file.fetch_scores(chrom, pos, pos)
        if not scores:
            self._freq_not_found(aline)
            return
        variant = variant.details.cshl_variant

        for index, score_variant in enumerate(scores['variant']):
            if score_variant == variant:
                values = scores[self.freq_column]
                aline[self.freq_output] = values[index]


# class TMFile:
#     def __init__(self, fN):
#         self.fN = fN
#         self.F = gzip.open(self.fN, 'rt')
#         self.hdrL = self.F.readline().strip()
#         self.hdrCs = self.hdrL.split("\t")

#         self.chrCI = self.hdrCs.index("chr")
#         self.posCI = self.hdrCs.index("position")
#         self.varCI = self.hdrCs.index("variant")

#     def lines(self):
#         for ln in self.F:
#             if ln[0] == '#':
#                 continue
#             cs = ln.strip("\n\r").split('\t')

#             ch = cs[self.chrCI]
#             pos = int(cs[self.posCI])
#             chI = chrInd[ch]
#             vr = cs[self.varCI]
#             key = (chI, pos, vr)

#             yield (key, cs)

#     def close(self):
#         self.F.close()


# class DNVFile:
#     def __init__(self, fN):
#         self.fN = fN
#         self.F = open(self.fN)
#         self.hdrL = self.F.readline().strip()
#         self.hdrCs = self.hdrL.split("\t")

#         self.locCI = self.hdrCs.index("location")
#         self.varCI = self.hdrCs.index("variant")

#     def lines(self):
#         for ln in self.F:
#             if ln[0] == '#':
#                 continue
#             cs = ln.strip("\n\r").split('\t')

#             ch, pos = cs[self.locCI].split(":")
#             pos = int(pos)
#             chI = chrInd[ch]
#             vr = cs[self.varCI]
#             key = (chI, pos, vr)

#             yield (key, cs)

#     def close(self):
#         self.F.close()


# def openFile(fN):
#     if fN.endswith(".txt.bgz"):
#         return TMFile(fN)
#     else:
#         return DNVFile(fN)


# class IterativeAccess:
#     def __init__(self, fN, clmnN):
#         self.fN = fN
#         self.clmnN = clmnN
#         self.tmf = TMFile(fN)
#         self.tmfLines = self.tmf.lines()
#         self.clmnI = self.tmf.hdrCs.index(self.clmnN)
#         self.currKey = (-1, 0, 0)

#     def getV(self, k):
#         if self.currKey < k:
#             for self.currKey, self.currCs in self.tmfLines:
#                 if self.currKey >= k:
#                     break
#             if self.currKey < k:
#                 self.currKey = (100000, 0, 0)

#         if self.currKey == k:
#             return self.currCs[self.clmnI]
#         return

#     def close(self):
#         self.tmf.close()


# class DirectAccess:
#     def __init__(self, fN, clmnN):
#         self.fN = fN
#         self.clmnN = clmnN
#         tmf = TMFile(fN)
#         self.clmnI = tmf.hdrCs.index(self.clmnN)
#         self.varI = tmf.varCI
#         tmf.close()
#         self.F = pysam.Tabixfile(self.fN)

#     def getV(self, k):
#         chI, pos, vr = k
#         ch = chrName[chI]

#         try:
#             for l in self.F.fetch(ch, pos-1, pos):
#                 cs = l.strip("\n\r").split("\t")
#                 if vr != cs[self.varI]:
#                     continue
#                 return cs[self.clmnI]
#         except ValueError:
#             pass
#         return

#     def close(self):
#         self.F.close()


# if __name__ == "__main__":
#     tFN = "/home/iossifov/work/T115/data-dev/bbbb/" \
#         "IossifovWE2014/Supplement-T2-eventsTable-annot.txt"
#     if len(sys.argv) > 1:
#         tFN = sys.argv[1]

#     accessMode = "direct"
#     if len(sys.argv) > 2:
#         accessMode = sys.argv[2]

#     freqAttFN = vDB._config.get("DEFAULT", "wd") + "/freqAtts.txt"
#     if len(sys.argv) > 3:
#         freqAttFN = sys.argv[3]

#     modeConstructor = {
#         "direct": DirectAccess,
#         "iterative": IterativeAccess
#     }

#     tF = openFile(tFN)

#     outHdr = list(tF.hdrCs)
#     freqAttF = open(freqAttFN)

#     fFS = []
#     for l in freqAttF:
#         ffN, tAN, fAT = l.strip().split("\t")
#         try:
#             tANI = tF.hdrCs.index(tAN)
#         except ValueError:
#             tANI = -1
#             outHdr.append(tAN)

#         AF = modeConstructor[accessMode](
#             vDB._config.get("DEFAULT", "studyDir") + "/" + ffN,
#             fAT)
#         fFS.append((AF, tANI))

#     print("\t".join(outHdr))

#     for tk, tcs in tF.lines():
#         for AF, tANI in fFS:
#             v = AF.getV(tk)
#             if not v:
#                 v = ""
#             if tANI == -1:
#                 tcs.append(v)
#             else:
#                 tcs[tANI] = v
#         print("\t".join(tcs))
