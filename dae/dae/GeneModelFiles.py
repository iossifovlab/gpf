#!/usr/bin/env python
import gzip
import pickle
import os
from collections import defaultdict, namedtuple

import pandas as pd

from dae.RegionOperations import Region


#
# Exon
#
class Exon:
    def __init__(
        self,
        start=None,
        stop=None,
        frame=None,
        number=None,
        cds_start=None,
        cds_stop=None,
    ):
        self.start = start
        self.stop = stop
        self.frame = frame  # related to cds

        # for GTF
        self.number = number  # exon number
        self.cds_start = cds_start  #
        self.cds_stop = cds_stop


class TranscriptModel:
    def __init__(
        self,
        gene=None,
        tr_id=None,
        tr_name=None,
        chrom=None,
        cds=[],
        strand=None,
        exons=[],
        tx=None,
        utrs=[],
        start_codon=None,
        stop_codon=None,
        is_coding=False,
        attributes={},
    ):
        self.gene = gene
        self.tr_id = tr_id
        self.tr_name = tr_name
        self.chrom = chrom
        self.cds = cds
        self.strand = strand
        self.exons = exons
        self.tx = tx

        # for GTF
        self.utrs = utrs
        self.start_codon = start_codon
        self.stop_codon = stop_codon

        self._is_coding = (
            is_coding  # it can be derivable from cds' start and end
        )
        self.attributes = attributes

    def is_coding(self):
        if self.cds[0] >= self.cds[1]:
            return False
        return True

    def CDS_regions(self, ss=0):

        if self.cds[0] >= self.cds[1]:
            return []

        cds_regions = []
        k = 0
        while self.exons[k].stop < self.cds[0]:
            k += 1

        if self.cds[1] <= self.exons[k].stop:
            cds_regions.append(
                Region(chrom=self.chrom, start=self.cds[0], stop=self.cds[1])
            )
            return cds_regions

        cds_regions.append(
            Region(
                chrom=self.chrom,
                start=self.cds[0],
                stop=self.exons[k].stop + ss,
            )
        )
        k += 1
        while k < len(self.exons) and self.exons[k].stop <= self.cds[1]:
            if self.exons[k].stop < self.cds[1]:
                cds_regions.append(
                    Region(
                        chrom=self.chrom,
                        start=self.exons[k].start - ss,
                        stop=self.exons[k].stop + ss,
                    )
                )
                k += 1
            else:
                cds_regions.append(
                    Region(
                        chrom=self.chrom,
                        start=self.exons[k].start - ss,
                        stop=self.exons[k].stop,
                    )
                )
                return cds_regions

        if k < len(self.exons) and self.exons[k].start <= self.cds[1]:
            cds_regions.append(
                Region(
                    chrom=self.chrom,
                    start=self.exons[k].start - ss,
                    stop=self.cds[1],
                )
            )

        return cds_regions

    def UTR5_regions(self):

        if self.cds[0] >= self.cds[1]:
            return []

        utr5_regions = []
        k = 0
        if self.strand == "+":
            while self.exons[k].stop < self.cds[0]:
                utr5_regions.append(
                    Region(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.exons[k].stop,
                    )
                )
                k += 1
            if self.exons[k].start < self.cds[0]:
                utr5_regions.append(
                    Region(
                        chr=self.chrom,
                        start=self.exons[k].start,
                        stop=self.cds[0] - 1,
                    )
                )

        else:
            while self.exons[k].stop < self.cds[1]:
                k += 1
            if self.exons[k].stop == self.cds[1]:
                k += 1
            else:
                utr5_regions.append(
                    Region(
                        chrom=self.chrom,
                        start=self.cds[1] + 1,
                        stop=self.exons[k].stop,
                    )
                )
                k += 1

            for e in self.exons[k:]:
                utr5_regions.append(
                    Region(chrom=self.chrom, start=e.start, stop=e.stop)
                )

        return utr5_regions

    def UTR3_regions(self):
        if self.cds[0] >= self.cds[1]:
            return []

        utr3_regions = []
        k = 0
        if self.strand == "-":
            while self.exons[k].stop < self.cds[0]:
                utr3_regions.append(
                    Region(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.exons[k].stop,
                    )
                )
                k += 1
            if self.exons[k].start < self.cds[0]:
                utr3_regions.append(
                    Region(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.cds[0] - 1,
                    )
                )

        else:
            while self.exons[k].stop < self.cds[1]:
                k += 1
            if self.exons[k].stop == self.cds[1]:
                k += 1
            else:
                utr3_regions.append(
                    Region(
                        chrom=self.chrom,
                        start=self.cds[1] + 1,
                        stop=self.exons[k].stop,
                    )
                )
                k += 1

            for e in self.exons[k:]:
                utr3_regions.append(
                    Region(chrom=self.chrom, start=e.start, stop=e.stop)
                )

        return utr3_regions

    def all_regions(self, ss=0, prom=0):

        all_regions = []

        if ss == 0:
            for e in self.exons:
                all_regions.append(
                    Region(chrom=self.chrom, start=e.start, stop=e.stop)
                )

        else:
            for e in self.exons:
                if e.stop <= self.cds[0]:
                    all_regions.append(
                        Region(chrom=self.chrom, start=e.start, stop=e.stop)
                    )
                elif e.start <= self.cds[0]:
                    if e.stop >= self.cds[1]:
                        all_regions.append(
                            Region(
                                chrom=self.chrom, start=e.start, stop=e.stop
                            )
                        )
                    else:
                        all_regions.append(
                            Region(
                                chrom=self.chrom,
                                start=e.start,
                                stop=e.stop + ss,
                            )
                        )
                elif e.start > self.cds[1]:
                    all_regions.append(
                        Region(chrom=self.chrom, start=e.start, stop=e.stop)
                    )
                else:
                    if e.stop >= self.cds[1]:
                        all_regions.append(
                            Region(
                                chrom=self.chrom,
                                start=e.start - ss,
                                stop=e.stop,
                            )
                        )
                    else:
                        all_regions.append(
                            Region(
                                chrom=self.chrom,
                                start=e.start - ss,
                                stop=e.stop + ss,
                            )
                        )

        if prom != 0:
            if self.strand == "+":
                all_regions[0] = Region(
                    chrom=all_regions[0].chrom,
                    start=all_regions[0].start - prom,
                    stop=all_regions[0].stop,
                )
            else:
                all_regions[-1] = Region(
                    chrom=all_regions[-1].chrom,
                    start=all_regions[-1].start,
                    stop=all_regions[-1].stop + prom,
                )

        return all_regions

    def total_len(self):
        length = 0
        for reg in self.exons:
            length += reg.stop - reg.start + 1
        return length

    def CDS_len(self):
        cds_region = self.CDS_regions()
        length = 0
        for reg in cds_region:
            length += reg.stop - reg.start + 1
        return length

    def UTR3_len(self):
        utr3 = self.UTR3_regions()
        length = 0
        for reg in utr3:
            length += reg.stop - reg.start + 1

        return length

    def UTR5_len(self):
        utr5 = self.UTR5_regions()
        length = 0
        for reg in utr5:
            length += reg.stop - reg.start + 1

        return length

    def calc_frames(self):
        length = len(self.exons)
        fms = []

        if self.cds[0] > self.cds[1]:
            fms = [-1] * length
        elif self.strand == "+":
            k = 0
            while self.exons[k].stop < self.cds[0]:
                fms.append(-1)
                k += 1
            fms.append(0)
            if self.exons[k].stop < self.cds[1]:
                fms.append((self.exons[k].stop - self.cds[0] + 1) % 3)
                k += 1
            while self.exons[k].stop < self.cds[1] and k < length:
                fms.append(
                    (fms[k] + self.exons[k].stop - self.exons[k].start + 1) % 3
                )
                k += 1
            fms += [-1] * (length - len(fms))
        else:
            k = length - 1
            while self.exons[k].start > self.cds[1]:
                fms.append(-1)
                k -= 1
            fms.append(0)
            if self.cds[0] < self.exons[k].start:
                fms.append((self.cds[1] - self.exons[k].start + 1) % 3)
                k -= 1
            while self.cds[0] < self.exons[k].start and k > -1:
                fms.append(
                    (fms[-1] + self.exons[k].stop - self.exons[k].start + 1)
                    % 3
                )
                k -= 1
            fms += [-1] * (length - len(fms))
            fms = fms[::-1]

        assert len(self.exons) == len(fms)
        return fms

    def update_frames(self):
        fms = self.calc_frames()
        for e, f in zip(self.exons, fms):
            e.frame = f

    def test_frames(self, update=False):
        fms = self.calc_frames()
        for e, f in zip(self.exons, fms):
            if e.frame != f:
                return False
        return True


# column names that expected to have on certain formats
# in order
Columns4FileFormat = {
    "commonGTF": "seqname,source,feature,start,end,score,strand,phase,"
    "attributes,comments".split(","),
    "commonDefault": "chr,trID,gene,strand,txBeg,txEnd,cdsStart,cdsEnd,"
    "exonStarts,exonEnds,exonFrames,atts".split(","),
    "commonGenePredUCSC": "name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,"
    "exonStarts,exonEnds".split(","),
    "ucscGenePred": "name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,"
    "exonCount,exonStarts,exonEnds".split(","),
    "refSeq": "bin,name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,"
    "exonCount,exonStarts,exonEnds,score,name2,"
    "cdsStartStat,cdsEndStat,exonFrames".split(","),
    "refFlat": "geneName,name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,"
    "exonCount,exonStarts,exonEnds".split(","),
    "knownGene": "name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,"
    "exonCount,exonStarts,exonEnds,proteinID,alignID".split(","),
    "ccds": "bin,name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,"
    "exonCount,exonStarts,exonEnds,score,name2,cdsStartStat,cdsEndStat,"
    "exonFrames".split(","),
}


# FILE_FORMAT_COLUMNS = {}


#
# GeneModel's database
#
class GeneModelDB:
    def __init__(self, name=None, location=None):
        self.name = name
        self.location = location
        self._shift = None
        self._alternative_names = None

        self._utrModels = {}
        self.transcriptModels = {}
        self._geneModels = defaultdict(list)

    # from orgininal without editing
    def addModelToDict(self, tm):

        assert tm.tr_id not in self.transcriptModels

        self.transcriptModels[tm.tr_id] = tm
        self._geneModels[tm.gene].append(tm)

        try:
            self._utrModels[tm.chrom][tm.tx].append(tm)
        except KeyError as e:
            if e.args[0] == tm.chrom:
                self._utrModels[tm.chrom] = {}
            self._utrModels[tm.chrom][tm.tx] = [tm]

        return -1

    def _updateIndexes(self):
        self._geneModels = defaultdict(list)
        self._utrModels = defaultdict(lambda: defaultdict(list))
        for tm in self.transcriptModels.values():
            self._geneModels[tm.gene].append(tm)
            self._utrModels[tm.chrom][tm.tx].append(tm)

    def gene_names(self):
        if self._geneModels is None:
            print(
                "Gene Models haven't been created/uploaded yet! "
                "Use either loadGeneModels function or "
                "self.createGeneModelDict function"
            )
            return None

        return self._geneModels.keys()

    def gene_models_by_gene_name(self, name):
        return self._geneModels.get(name, None)

    def gene_models_by_location(self, chr, pos1, pos2=None):
        R = []

        if pos2 is None:
            for key in self._utrModels[chr]:
                if pos1 >= key[0] and pos1 <= key[1]:
                    R.extend(self._utrModels[chr][key])

        else:
            if pos2 < pos1:
                pos1, pos2 = pos2, pos1

            for key in self._utrModels[chr]:
                if (pos1 <= key[0] and pos2 >= key[0]) or (
                    pos1 >= key[0] and pos1 <= key[1]
                ):
                    R.extend(self._utrModels[chr][key])

        return R

    def relabel_chromosomes_chr(self, Relabel):

        if self.transcriptModels is None:
            print(
                "Gene Models haven't been created/uploaded yet! "
                "Use either loadGeneModels function or "
                "self.createGeneModelDict function"
            )
            return None

        for chrom in self._utrModels.keys():

            try:
                self._utrModels[Relabel[chrom]] = self._utrModels[chrom]
                self._utrModels.pop(chrom)
            except KeyError:
                pass

        for trID in self.transcriptModels:
            try:
                self.transcriptModels[trID].chr = Relabel[
                    self.transcriptModels[trID].chr
                ]
            except KeyError:
                pass

    def relabel_chromosomes(self, file="ucsc2gatk.txt"):

        if self.transcriptModels is None:
            print(
                "Gene Models haven't been created/uploaded yet! "
                "Use either loadGeneModels function or "
                "self.createGeneModelDict function"
            )
            return None

        f = open(file)
        relabel = dict([(line.split()[0], line.split()[1]) for line in f])

        for chrom in self._utrModels.keys():

            try:
                self._utrModels[relabel[chrom]] = self._utrModels[chrom]
                self._utrModels.pop(chrom)
            except KeyError:
                pass

        for trID in self.transcriptModels:
            try:
                self.transcriptModels[trID].chr = relabel[
                    self.transcriptModels[trID].chrom
                ]
            except KeyError:
                pass

    def save(self, outputFile, gzipped=True):
        if gzipped:
            f = gzip.open(outputFile + ".gz", "wt")
        else:
            f = open(outputFile, "wt")

        f.write(
            "\t".join(
                "chr trID gene strand tsBeg txEnd cdsStart cdsEnd "
                "exonStarts exonEnds exonFrames atts".split()
            )
            + "\n"
        )

        for tmId, tm in sorted(self.transcriptModels.items()):
            eStarts = ",".join([str(e.start) for e in tm.exons])
            eEnds = ",".join([str(e.stop) for e in tm.exons])
            eFrames = ",".join([str(e.frame) for e in tm.exons])

            add_atts = ";".join(
                [k + ":" + str(v) for k, v in list(tm.attr.items())]
            )

            cs = [
                tm.chrom,
                tm.tr_id,
                tm.gene,
                tm.strand,
                tm.tx[0],
                tm.tx[1],
                tm.cds[0],
                tm.cds[1],
                eStarts,
                eEnds,
                eFrames,
                add_atts,
            ]
            f.write(
                "\t".join([str(x) if x is not None else "" for x in cs]) + "\n"
            )
        f.close()


def openFile(fileName):
    if fileName.endswith(".gz") or fileName.endswith(".bgz"):
        inF = gzip.open(fileName, "rt")
    else:
        inF = open(fileName)

    return inF


class GtfFileReader:
    colNames = (
        "seqname,source,feature,start,end,score,strand,phase,"
        "attributes,comments".split(",")
    )

    @staticmethod
    def gtfParseAttr(stx, delim=" "):
        atx = {}
        for x in stx.strip(" ;").split(";"):
            dx = [w for w in x.split(delim) if w != ""]

            if not dx:
                continue
            n, d = dx
            d = d.strip('"')

            if n in atx:
                try:
                    atx[n].append(d)
                except AttributeError:
                    atx[n] = [atx[n], d]
            else:
                atx[n] = d
        return atx

    @staticmethod
    def gtfParseStr(line):
        terms = line.strip("\n").split("\t")
        rx = {h: d for h, d in zip(GtfFileReader.colNames, terms)}

        rx["start"] = int(rx["start"])
        rx["end"] = int(rx["end"])
        rx["attributes"] = GtfFileReader.gtfParseAttr(rx["attributes"])

        return rx

    def __init__(self, fileName, delim=" "):
        #
        # GTF: space delimiter
        # GFF: =     delimiter
        self.colIndex = {
            self.colNames[n]: n for n in range(len(self.colNames))
        }

        self._file = None
        try:
            self._file = openFile(fileName)
        except IOError as e:
            print(e)
            return

    def __iter__(self):
        return self

    def __next__(self):
        line = self._file.readline()
        while line and (line[0] == "#"):
            line = self._file.readline()

        if line == "":
            raise StopIteration

        return GtfFileReader.gtfParseStr(line)  # rx

    # # TODO: delete after migrate to python3
    # # make code compatible to python2
    # def next(self):
    #     line = self._file.readline()
    #     while line and (line[0] == "#"):
    #         line = self._file.readline()

    #     if line == "":
    #         raise StopIteration

    #     return GtfFileReader.gtfParseStr(line)  # rx


class defaultFileReader:
    dftHead = Columns4FileFormat["commonDefault"]

    def __init__(self, line):
        self.hDict = {h: n for n, h in enumerate(line.strip("\n").split("\t"))}
        try:
            self.index = [self.hDict[h] for h in self.dftHead]
        except KeyError:
            self.index = [n for n in range(len(self.dftHead))]

    def read(self, line):
        terms = line.strip("\n").split("\t")
        return [terms[n] for n in self.index]


def defaultGeneModelParser(gm, file_name, gene_mapping_file=None):
    gm.location = file_name

    f = openFile(file_name)

    line = f.readline()
    lineR = defaultFileReader(line)
    for nLR, line in enumerate(f):

        cs = lineR.read(line)  # l[:-1].split('\t')

        (
            chrom,
            trID,
            gene,
            strand,
            txB,
            txE,
            cdsB,
            cdsE,
            eStarts,
            eEnds,
            eFrames,
            add_attrs,
        ) = cs

        exons = []
        for frm, sr, sp in zip(
            *map(lambda x: x.split(","), [eFrames, eStarts, eEnds])
        ):
            e = Exon(start=int(sr), stop=int(sp), frame=int(frm))
            exons.append(e)

        if add_attrs:
            attrs = dict([a.split(":") for a in add_attrs.split(";")])
        else:
            attrs = {}

        tm = TranscriptModel()
        tm.gene = gene
        tm.tr_id = trID
        tm.tr_name = trID
        tm.chrom = chrom
        tm.strand = strand
        tm.tx = (int(txB), int(txE))
        tm.cds = (int(cdsB), int(cdsE))
        tm.exons = exons
        tm.attr = attrs

        gm.transcriptModels[tm.tr_id] = tm

    f.close()
    gm._updateIndexes()


def load_default_gene_models_format(filename, gene_mapping_file=None):
    df = pd.read_csv(filename, sep="\t")
    expected_columns = [
        "chr",
        "trID",
        "gene",
        "strand",
        "tsBeg",
        "txEnd",
        "cdsStart",
        "cdsEnd",
        "exonStarts",
        "exonEnds",
        "exonFrames",
        "atts",
    ]

    assert set(expected_columns) <= set(df.columns)
    if "trOrigID" not in df.columns:
        tr_names = pd.Series(data=df["trID"].values)
        df["trOrigID"] = tr_names

    gm = GeneModelDB(location=filename)

    records = df.to_dict(orient="records")
    for line in records:
        exon_starts = list(map(int, line["exonStarts"].split(",")))
        exon_ends = list(map(int, line["exonEnds"].split(",")))
        exon_frames = list(map(int, line["exonFrames"].split(",")))
        assert len(exon_starts) == len(exon_ends) == len(exon_frames)
        exons = []
        for start, end, frame in zip(exon_starts, exon_ends, exon_frames):
            exons.append(Exon(start=start, stop=end, frame=frame))
        attributes = {}
        if line.get("atts") is not None:
            attributes = dict(
                [a.split(":") for a in line.get("atts").split(";")]
            )
        tm = TranscriptModel(
            gene=line["gene"],
            tr_id=line["trID"],
            tr_name=line["trOrigID"],
            chrom=line["chr"],
            strand=line["strand"],
            tx=(line["tsBeg"], line["txEnd"]),
            cds=(line["cdsStart"], line["cdsEnd"]),
            exons=exons,
            attributes=attributes,
        )
        gm.addModelToDict(tm)

    gm._updateIndexes()
    return gm


def pickledGeneModelParser(gm, file_name, gene_mapping_file=None):
    import pickle

    gm.location = file_name
    pkl_file = open(file_name, "rb")
    gm._utrModels, gm.transcriptModels, gm._geneModels = pickle.load(pkl_file)
    pkl_file.close()


def gtfGeneModelParser(gm, file_name, gene_mapping_file=None):
    gm.name = "GTF"
    # print( 'GeneModel format: ', gm.name, '\timporting: ',
    # file_name, file=sys.stderr )
    gm.location = file_name

    f = GtfFileReader(file_name)
    for nLR, rx in enumerate(f):
        if rx["feature"] in ["gene"]:
            continue

        # if 'transcript_support_level' in rx['attributes']  and
        # rx['attributes']['transcript_support_level'] != '1': continue

        trID = rx["attributes"]["transcript_id"]
        if rx["feature"] in ["transcript", "Selenocysteine"]:
            if (
                rx["feature"] in ["Selenocysteine"]
                and trID in gm.transcriptModels
            ):
                continue

            if trID in gm.transcriptModels:
                raise Exception(
                    "{} of {}: already existed on transcriptModels".format(
                        trID, rx["feature"]
                    )
                )

            tm = TranscriptModel()
            tm.gene = rx["attributes"]["gene_name"]
            tm.tr_id = trID
            tm.chrom = rx["seqname"]
            tm.strand = rx["strand"]
            tm.tx = (rx["start"], rx["end"])
            tm.cds = (rx["end"], rx["start"])
            tm.attr = rx["attributes"]

            gm.addModelToDict(tm)
            # gm.transcriptModels[tm.tr_id] = tm
            continue

        if rx["feature"] in ["CDS", "exon"]:
            if trID not in gm.transcriptModels:
                raise Exception(
                    "{}: exon or CDS not existed on transcriptModels".format(
                        trID
                    )
                )

            ix = (
                int(rx["attributes"]["exon_number"]) - 1
            )  # 1-based to 0-based indexing
            # print trID, len(gm.transcriptModels[trID].exons), ix,
            # rx['attributes']['exon_number']
            if len(gm.transcriptModels[trID].exons) <= ix:
                gm.transcriptModels[trID].exons.append(Exon())

            if rx["feature"] == "exon":
                gm.transcriptModels[trID].exons[ix].start = rx["start"]
                gm.transcriptModels[trID].exons[ix].stop = rx["end"]
                gm.transcriptModels[trID].exons[ix].frame = -1
                gm.transcriptModels[trID].exons[ix].number = (
                    ix + 1
                )  # return to 1-base indexing

                continue

            if rx["feature"] == "CDS":
                gm.transcriptModels[trID].exons[ix].cds_start = rx["start"]
                gm.transcriptModels[trID].exons[ix].cds_stop = rx["end"]
                gm.transcriptModels[trID].exons[ix].frame = int(rx["phase"])

                gm.transcriptModels[trID]._is_coding = True

                # cx = gm.transcriptModels[trID].cds
                # gm.transcriptModels[trID].cds =
                # (min(cx[0],rx['start']), max(cx[1],rx['end']))

                continue

        if rx["feature"] in [
            "UTR",
            "5UTR",
            "3UTR",
            "start_codon",
            "stop_codon",
        ]:
            ix = int(rx["attributes"]["exon_number"])  # 1-based
            if "UTR" in rx["feature"]:
                gm.transcriptModels[trID].utrs.append(
                    (rx["start"], rx["end"], ix)
                )
                continue

            if rx["feature"] == "start_codon":
                gm.transcriptModels[trID].start_codon = (
                    rx["start"],
                    rx["end"],
                    ix,
                )
            if rx["feature"] == "stop_codon":
                gm.transcriptModels[trID].stop_codon = (
                    rx["start"],
                    rx["end"],
                    ix,
                )

            cx = gm.transcriptModels[trID].cds
            gm.transcriptModels[trID].cds = (
                min(cx[0], rx["start"]),
                max(cx[1], rx["end"]),
            )

            continue

        raise Exception("unknown {} found".format(rx["feature"]))

    for k in gm.transcriptModels.keys():
        tm = gm.transcriptModels[k]
        tm.exons = sorted(tm.exons, key=lambda x: x.start)
        tm.utrs = sorted(tm.utrs, key=lambda x: x[0])
        tm.update_frames()

    # TODO: no needed: done by gm.addModelToDict(tm)
    # for k, gx in gm.transcriptModels.items():
    #   gID = gx.gene
    #   if gID not in gm._geneModels: gm._geneModels[gID] = []
    #
    #   gm._geneModels[gID].append( gx )


#
#  MT chromosome
#
def mitoGeneModelParser(gm, file_name, gene_mapping_file=None):
    gm.name = "mitomap"
    gm._alternative_names = None

    gm._utrModels["chrM"] = {}
    file = openFile(file_name)

    mode = None

    for line in file:
        line = line.split()
        if line[0] == "#":
            mode = line[1]
            continue

        if mode not in ["cds", "rRNAs", "tRNAs"]:
            continue

        mm = TranscriptModel()
        mm.gene = mm.tr_id = line[0]
        mm.chr = "chrM"
        mm.strand = line[1]
        mm.tx = (int(line[2]), int(line[3]))
        mm.attr = {}

        e = Exon()
        e.start = int(line[2])
        e.stop = int(line[3])

        if mode == "cds":
            mm.cds = (int(line[2]), int(line[3]))
            e.frame = 0

        elif mode == "rRNAs":
            mm.cds = (int(line[2]), int(line[2]))
            e.frame = -1

        elif mode == "tRNAs":
            mm.cds = (int(line[2]), int(line[2]))
            mm.attr["anticodonB"] = line[4]
            mm.attr["anticodonE"] = line[5]
            e.frame = -1
        # commented on original ewa version
        # elif mode == "regulatory_elements":
        #   mm.cds = (int(line[2]), int(line[2]))
        #   mm.tx = (int(line[1]), int(line[2]))
        # note about original: line is different from others
        #   mm.exons = []

        else:  # TODO: something wrong message
            continue  # impossible to happen

        mm.exons = [e]

        gm._utrModels["chrM"][mm.tx] = [mm]
        gm.transcriptModels[mm.tr_id] = mm
        gm._geneModels[mm.gene] = [mm]

    file.close()


class parserLine4UCSC_genePred:
    commonCols = Columns4FileFormat["commonGenePredUCSC"]

    def __init__(self, header):
        """
        header: list of column names
           name,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,exonStarts,exonEnds
        required
     """
        self.header = header
        self.idxHD = {n: i for i, n in enumerate(self.header)}

    def parse(self, line):
        """
       reading tab-delimited line
       return:  1) transcriptModel without gene name
                2) parsed data in dict format
     """
        terms = line.strip("\n").split("\t")

        assert len(terms) == len(self.header)

        cs = {k: v for k, v in zip(self.header, terms)}

        tm = TranscriptModel()

        # tm.gene   = # TODO implimented outside
        tm.tr_id = cs["name"]
        tm.chrom = cs["chrom"]
        tm.strand = cs["strand"]
        tm.tx = (int(cs["txStart"]) + 1, int(cs["txEnd"]))
        tm.cds = (int(cs["cdsStart"]) + 1, int(cs["cdsEnd"]))
        tm.exons = [
            Exon(b + 1, e)
            for b, e in zip(
                map(int, cs["exonStarts"].strip(",").split(",")),
                map(int, cs["exonEnds"].strip(",").split(",")),
            )
        ]

        tm.attr = {
            k: v
            for k, v in cs.items()
            if k not in parserLine4UCSC_genePred.commonCols
        }
        tm.update_frames()

        # trIdC[tm.tr_id] += 1                       #TODO implimented outside
        # tm.tr_id += "_" + str(trIdC[tm.tr_id])      #TODO implimented outside

        # cls.addModelToDict(tm)                   #TODO should be done outside
        return tm, cs


def geneMapping(fileName=None):
    """
      alternative names for genes
      assume that its first line has two column names
   """
    if not fileName:
        return {}

    inF = openFile(fileName)

    inF.readline()

    altName = {}
    for line in inF:
        k, v = line.strip("\n").split("\t")
        altName[k] = v

    return altName


def refSeqParser(gm, location=None, gene_mapping_file=None):
    colNames = Columns4FileFormat["refSeq"]
    lR = parserLine4UCSC_genePred(colNames)

    if not location:
        location = gm.location

    GMF = openFile(location)

    trIdC = defaultdict(int)
    for nLR, line in enumerate(GMF):
        if line[0] == "#":
            continue

        tm, cs = lR.parse(line)
        tm.gene = cs["name2"]

        trIdC[tm.tr_id] += 1
        tm.tr_id += "_" + str(trIdC[tm.tr_id])
        tm.update_frames()

        gm.addModelToDict(tm)

    GMF.close()


def refFlatParser(gm, file_name, gene_mapping_file="default"):
    assert gene_mapping_file == "default"

    # column names
    colNames = Columns4FileFormat["refFlat"]
    lR = parserLine4UCSC_genePred(colNames)

    GMF = openFile(file_name)

    trIdC = defaultdict(int)
    for nLR, line in enumerate(GMF):
        if line[0] == "#":
            hcs = line[1:].strip("\n\r").split("\t")
            if hcs != Columns4FileFormat["refFlat"]:
                raise Exception(
                    f"The file {file_name} doesn't look like a refFlat file"
                )

            continue

        tm, cs = lR.parse(line)
        tm.gene = cs["geneName"]

        trIdC[tm.tr_id] += 1
        tm.tr_id += "_" + str(trIdC[tm.tr_id])
        tm.update_frames()

        gm.addModelToDict(tm)

    GMF.close()


def knownGeneParser(gm, file_name, gene_mapping_file="default"):
    colNames = Columns4FileFormat["knownGene"]
    lR = parserLine4UCSC_genePred(colNames)

    if gene_mapping_file == "default":
        gene_mapping_file = os.path.join(
            os.path.dirname(file_name), "kgId2Sym.txt.gz"
        )

    gmf = openFile(file_name)

    trIdC = defaultdict(int)
    for nLR, line in enumerate(gmf):
        if line[0] == "#":
            continue

        tm, cs = lR.parse(line)
        try:
            tm.gene = gm._alternative_names[cs["name"]]
        except KeyError:
            tm.gene = cs["name"]

        trIdC[tm.tr_id] += 1
        tm.tr_id += "_" + str(trIdC[tm.tr_id])
        tm.update_frames()

        gm.addModelToDict(tm)

    gmf.close()


#  format = refseq
#  CCC = {"refseq":refseqParser, ....}
#  o = GeneModelDB()
#  CCC[format](o,file, geneMapFile)
#


# ccdsGene
def ccdsParser(gm, file_name, gene_mapping_file="default"):
    colNames = Columns4FileFormat["ccds"]
    lR = parserLine4UCSC_genePred(colNames)

    if gene_mapping_file == "default":
        gene_mapping_file = os.path.dirname(file_name) + "/ccdsId2Sym.txt.gz"

    gm._alternative_names = geneMapping(gene_mapping_file)

    GMF = openFile(file_name)

    trIdC = defaultdict(int)
    for nLR, line in enumerate(GMF):
        if line[0] == "#":
            continue

        tm, cs = lR.parse(line)
        try:
            tm.gene = gm._alternative_names[cs["name"]]
        except KeyError:
            tm.gene = cs["name"]

        trIdC[tm.tr_id] += 1
        tm.tr_id += "_" + str(trIdC[tm.tr_id])
        tm.update_frames()

        gm.addModelToDict(tm)

    GMF.close()


def ucscGenePredParser(gm, file_name, gene_mapping_file="default"):
    colNames = Columns4FileFormat["ucscGenePred"]
    lR = parserLine4UCSC_genePred(colNames)

    if gene_mapping_file != "default":
        gm._alternative_names = geneMapping(gene_mapping_file)

    GMF = openFile(file_name)

    trIdC = defaultdict(int)
    for nLR, line in enumerate(GMF):
        if line[0] == "#":
            continue

        tm, cs = lR.parse(line)
        try:
            tm.gene = gm._alternative_names[cs["name"]]
        except (KeyError, TypeError):
            tm.gene = cs["name"]

        trIdC[tm.tr_id] += 1
        tm.tr_id += "_" + str(trIdC[tm.tr_id])
        tm.update_frames()

        gm.addModelToDict(tm)

    GMF.close()


FORMAT = namedtuple("format", "name parser")

KNOWN_FORMAT = {
    "refFlat.txt.gz": FORMAT(*["refflat", refFlatParser]),
    "refflat": FORMAT(*["refflat", refFlatParser]),
    "refGene.txt.gz": FORMAT(*["refseq", refSeqParser]),
    "refseq": FORMAT(*["refseq", refSeqParser]),
    "ccdsGene.txt.gz": FORMAT(*["ccds", ccdsParser]),
    "ccds": FORMAT(*["ccds", ccdsParser]),
    "knownGene.txt.gz": FORMAT(*["knowngene", knownGeneParser]),
    "knowngene": FORMAT(*["knowngene", knownGeneParser]),
    "gtf": FORMAT(*["gtf", gtfGeneModelParser]),
    "pickled": FORMAT(*["pickled", pickledGeneModelParser]),
    "mitomap.txt": FORMAT(*["mito", mitoGeneModelParser]),
    # "mito": FORMAT(*["mito", mitoGeneModelParser]),
    "default": FORMAT(*["default", defaultGeneModelParser]),
    "ucscgenepred": FORMAT(*["ucscgenepred", ucscGenePredParser]),
}
# fmt: off
KNOWN_FORMAT_NAME = \
    "refflat,refseq,ccds,knowngene,gtf,pickled," \
    "default,ucscgenepred".split(",")   # "mito," \
# fmt: on


def infer_format(file_name="refGene.txt.gz", file_format=None):
    acceptedFormat = []

    known_formats = KNOWN_FORMAT_NAME
    if file_format:
        known_formats = [file_format]

    for format_name in known_formats:
        gm = GeneModelDB()
        fm = KNOWN_FORMAT[format_name]
        print("trying format parser:", format_name)
        try:
            print("trying format parser:", fm.name)
            fm.parser(gm, file_name, gene_mapping_file="default")
        except Exception:
            # import traceback
            # traceback.print_exc()
            continue

        acceptedFormat.append(format_name)

    if len(acceptedFormat) != 1:
        accepted_formats = ",".join(acceptedFormat)
        raise Exception(
            f"[{file_name}:'{accepted_formats}'] non-mataching/more "
            f"than 1 match/match-not-found "
            f"from known formats [{known_formats}]\nplease specify by "
            f"--TrawFormat"
        )

    acceptedFormat = acceptedFormat[0]
    if (file_name.endswith(".gtf") or file_name.endswith(".gtf.gz")) and (
        acceptedFormat != "gtf"
    ):
        raise Exception("{} is not GTF format".format(file_name))

    if file_name.endswith(".dump") and (acceptedFormat != "pickled"):
        raise Exception('{} is not "pickled" format'.format(file_name))

    fn = file_name.split("/")[-1]
    if fn in KNOWN_FORMAT:
        fm = KNOWN_FORMAT[fn].name
        if fm != acceptedFormat:
            raise Exception(
                '"{}:{}": conflict with Database [{}:{}]'.format(
                    fn, acceptedFormat, fn, fm
                )
            )

    return acceptedFormat


def load_gene_models(
    file_name="/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz",
    gene_mapping_file="default",
    format=None,
):

    fm = KNOWN_FORMAT[infer_format(file_name, file_format=format)]

    gm = GeneModelDB()
    gm.location = file_name
    fm.parser(gm, file_name, gene_mapping_file)

    return gm


def save_pickled_dicts(gm, outputFile="./geneModels"):
    pickle.dump(
        [gm._utrModels, gm.transcriptModels, gm._geneModels],
        open(outputFile + ".dump", "wb"),
        2,
    )


# def create_region(chrom, b, e):
#     reg = namedtuple("reg", "start stop chr")

#     return reg(chr=chrom, start=b, stop=e)


def join_gene_models(*gene_models):

    if len(gene_models) < 2:
        raise Exception("The function needs at least 2 arguments!")

    gm = GeneModelDB()
    gm._utrModels = {}
    gm._geneModels = {}

    gm.transcriptModels = gene_models[0].transcriptModels.copy()

    for i in gene_models[1:]:
        gm.transcriptModels.update(i.transcriptModels)

    gm._updateIndexes()

    return gm


if __name__ == "__main__":
    fn = "../../../tests/gtf/genePred.gtf"
    gm = GeneModelDB()
    print(gtfGeneModelParser(gm, fn))
    print(infer_format(fn))
    load_gene_models(fn)
