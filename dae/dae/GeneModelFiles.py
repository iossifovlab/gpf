#!/bin/env python

# July 12th 2013
# written by Ewa

from dae.RegionOperations import Region, collapse_noChr
import gzip
import pickle
import sys
from typing import Dict, List, Any
from collections import defaultdict, namedtuple, OrderedDict


class TranscriptModel(object):

    attr: Dict[str, Any] = {}
    gene = None
    trID = None
    chr = None
    cds: List = []
    strand = None
    exons: List = []
    tx: List = []

    def is_coding(self):
        if self.cds[0] >= self.cds[1]:
            return False
        return True

    def CDS_regions(self, ss=0):

        if self.cds[0] >= self.cds[1]:
            return []

        CDS_regions = []
        k = 0
        while self.exons[k].stop < self.cds[0]:
            k += 1

        if self.cds[1] <= self.exons[k].stop:
            CDS_regions.append(Region(self.chr, self.cds[0], self.cds[1]))
            return CDS_regions

        CDS_regions.append(
            Region(self.chr, self.cds[0], self.exons[k].stop + ss)
        )
        k += 1
        while k < len(self.exons) and self.exons[k].stop <= self.cds[1]:
            if self.exons[k].stop < self.cds[1]:
                CDS_regions.append(
                    Region(
                        self.chr,
                        self.exons[k].start - ss,
                        stop=self.exons[k].stop + ss,
                    )
                )
                k += 1
            else:
                CDS_regions.append(
                    Region(
                        self.chr,
                        self.exons[k].start - ss,
                        stop=self.exons[k].stop,
                    )
                )
                return CDS_regions

        if k < len(self.exons) and self.exons[k].start <= self.cds[1]:
            CDS_regions.append(
                Region(self.chr, self.exons[k].start - ss, stop=self.cds[1])
            )

        return CDS_regions

    def UTR5_regions(self):

        if self.cds[0] >= self.cds[1]:
            return []

        utr5_regions = []
        k = 0
        if self.strand == "+":
            while self.exons[k].stop < self.cds[0]:
                utr5_regions.append(
                    Region(
                        chrom=self.chr,
                        start=self.exons[k].start,
                        stop=self.exons[k].stop,
                    )
                )
                k += 1
            if self.exons[k].start < self.cds[0]:
                utr5_regions.append(
                    Region(
                        chrom=self.chr,
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
                        chrom=self.chr,
                        start=self.cds[1] + 1,
                        stop=self.exons[k].stop,
                    )
                )
                k += 1

            for e in self.exons[k:]:
                utr5_regions.append(
                    Region(chrom=self.chr, start=e.start, stop=e.stop)
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
                        chrom=self.chr,
                        start=self.exons[k].start,
                        stop=self.exons[k].stop,
                    )
                )
                k += 1
            if self.exons[k].start < self.cds[0]:
                utr3_regions.append(
                    Region(
                        chrom=self.chr,
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
                        chrom=self.chr,
                        start=self.cds[1] + 1,
                        stop=self.exons[k].stop,
                    )
                )
                k += 1

            for e in self.exons[k:]:
                utr3_regions.append(
                    Region(chrom=self.chr, start=e.start, stop=e.stop)
                )

        return utr3_regions

    def all_regions(self, ss=0, prom=0):

        all_regions = []

        if ss == 0:
            for e in self.exons:
                all_regions.append(
                    Region(chrom=self.chr, start=e.start, stop=e.stop)
                )
        else:
            for e in self.exons:
                if e.stop <= self.cds[0]:
                    all_regions.append(
                        Region(chrom=self.chr, start=e.start, stop=e.stop)
                    )
                elif e.start <= self.cds[0]:
                    if e.stop >= self.cds[1]:
                        all_regions.append(
                            Region(chrom=self.chr, start=e.start, stop=e.stop)
                        )
                    else:
                        all_regions.append(
                            Region(
                                chrom=self.chr, start=e.start, stop=e.stop + ss
                            )
                        )
                elif e.start > self.cds[1]:
                    all_regions.append(
                        Region(chrom=self.chr, start=e.start, stop=e.stop)
                    )
                else:
                    if e.stop >= self.cds[1]:
                        all_regions.append(
                            Region(
                                chrom=self.chr, start=e.start - ss, stop=e.stop
                            )
                        )
                    else:
                        all_regions.append(
                            Region(
                                chrom=self.chr,
                                start=e.start - ss,
                                stop=e.stop + ss,
                            )
                        )

        if prom != 0:
            if self.strand == "+":
                all_regions[0] = Region(
                    chrom=all_regions[0].chr,
                    start=all_regions[0].start - prom,
                    stop=all_regions[0].stop,
                )
            else:
                all_regions[-1] = Region(
                    chrom=all_regions[-1].chr,
                    start=all_regions[-1].start,
                    stop=all_regions[-1].stop + prom,
                )

        return all_regions

    def total_len(self):

        length = 0
        for e in self.exons:
            length += e.stop - e.start + 1
        return length

    def CDS_len(self):

        cds_region = self.CDS_regions()

        length = 0
        for c in cds_region:
            length += c.stop - c.start + 1
        return length

    def UTR3_len(self):

        utr3 = self.UTR3_regions()

        res = 0

        for i in utr3:
            res += i.stop - i.start + 1

        return res

    def UTR5_len(self):

        utr5 = self.UTR5_regions()
        res = 0
        for i in utr5:
            res += i.stop - i.start + 1
        return res

    def __check_if_exon(self, pos_start, pos_stop):

        for e in self.exons:
            if e.start > pos_stop:
                return False
            if (e.start <= pos_start <= e.stop) or (
                pos_start < e.start and pos_stop >= e.start
            ):
                return True
        return False

    def what_region(self, chr, pos_start, pos_stop, prom=0):
        if not self.is_coding():
            return "non-coding"

        if pos_stop < self.exons[0].start:
            if prom == 0:
                return "no_hit"
            if self.strand == "+" and pos_stop >= self.exons[0].start - prom:
                return "promoter"
            return "no_hit"

        if pos_start > self.exons[-1].stop:
            if prom == 0:
                return "no_hit"
            if self.strand == "-" and pos_start <= self.exons[-1].stop + prom:
                return "promoter"
            return "no_hit"

        if pos_stop < self.cds[0]:
            if self.__check_if_exon(pos_start, pos_stop):
                if self.strand == "+":
                    return "5'UTR"
                return "3'UTR"

            if self.strand == "+":
                return "5'UTR-intron"
            return "3'UTR-intron"

        if pos_start > self.cds[1]:
            if self.__check_if_exon(pos_start, pos_stop):
                if self.strand == "+":
                    return "3'UTR"
                return "5'UTR"

            if self.strand == "+":
                return "3'UTR-intron"
            return "5'UTR-intron"

        if (
            pos_start <= self.exons[0].start
            and pos_stop >= self.exons[-1].stop
        ):
            return "all"

        if self.__check_if_exon(pos_start, pos_stop):
            return "CDS"

        if self.chr != chr:
            return "no_hit"

        return "intronic"


class Exon(object):
    start = None
    stop = None
    frame = None


class GeneModels:
    def __init__(self):
        self.name = None
        self.location = None
        self._shift = None
        self._Alternative_names = None

        self._utrModels = OrderedDict()
        self.transcriptModels = OrderedDict()
        self._geneModels = OrderedDict
        self._Alternative_names = None

    def __addToDict(self, line):

        chrom = line[1 + self._shift]

        if self.name != "knowngene":
            if line[0] != "":
                bin = line[0]
            if line[13] != "":
                cdsStartStatus = line[13]
            if line[14] != "":
                cdsEndStatus = line[14]
            if line[11] != "":
                score = line[11]
            if self.name == "refseq":
                try:
                    gene = self._Alternative_names[line[12]]
                except Exception:
                    gene = line[12]
                trId = line[1]
                trName = trId + "_1"

            else:
                try:
                    gene = self._Alternative_names[line[1]]
                except Exception:
                    gene = line[1]
                trId = line[1]
                trName = trId + "_1"

            Frame = list(map(int, line[-1].split(",")[:-1]))

        else:
            if line[10] != "":
                proteinId = line[10]
            try:
                gene = self._Alternative_names[line[0]]
            except Exception:
                gene = line[0]
            trId = line[0]
            trName = trId + "_1"

        k = 1
        while True:
            try:
                self.transcriptModels[trName]
                k += 1
                trName = trId + "_" + str(k)
            except Exception:
                break

        strand = line[2 + self._shift]
        transcription_start = int(line[3 + self._shift])
        transcription_end = line[4 + self._shift]
        cds_start = line[5 + self._shift]
        cds_end = line[6 + self._shift]
        exon_starts = line[8 + self._shift].split(",")[:-1]
        exon_ends = line[9 + self._shift].split(",")[:-1]
        exon_count = int(line[7 + self._shift])

        ll = len(exon_starts)
        exons = []

        if self.name != "knowngene":

            for i in range(0, ll):
                ex = Exon()
                ex.start = int(exon_starts[i]) + 1
                ex.stop = int(exon_ends[i])
                ex.frame = int(Frame[i])
                exons.append(ex)
        else:
            Frame = []
            if int(cds_start) >= int(cds_end):
                for e in range(0, ll):
                    Frame.append(-1)

            elif strand == "+":
                k = 0
                while int(exon_ends[k]) < int(cds_start):
                    Frame.append(-1)
                    k += 1
                Frame.append(0)
                if int(cds_end) > int(exon_ends[k]):
                    Frame.append((int(exon_ends[k]) - int(cds_start)) % 3)
                if int(cds_end) <= int(exon_ends[k]):
                    for e in exon_ends[k + 1 :]:
                        Frame.append(-1)
                else:
                    k += 1
                    while k < ll and int(exon_ends[k]) < int(cds_end):
                        Frame.append(
                            (
                                Frame[k]
                                + int(exon_ends[k])
                                - int(exon_starts[k])
                            )
                            % 3
                        )
                        k += 1
                    k += 1
                    for e in exon_ends[k:]:
                        Frame.append(-1)

            else:
                k = len(exon_ends) - 1
                while int(exon_starts[k]) > int(cds_end):
                    Frame.append(-1)
                    k -= 1
                Frame.append(0)
                if int(cds_start) < int(exon_starts[k]):
                    Frame.append((int(cds_end) - int(exon_starts[k])) % 3)
                if int(cds_start) >= int(exon_starts[k]):
                    for e in exon_ends[:k]:
                        Frame.append(-1)
                else:
                    k -= 1
                    while k > -1 and int(exon_starts[k]) > int(cds_start):
                        Frame.append(
                            (
                                Frame[-1]
                                + int(exon_ends[k])
                                - int(exon_starts[k])
                            )
                            % 3
                        )
                        k -= 1
                    k -= 1
                    for e in exon_ends[: k + 1]:
                        Frame.append(-1)
                    Frame = Frame[::-1]

            for i in range(0, ll):
                ex = Exon()
                ex.start = int(exon_starts[i]) + 1
                ex.stop = int(exon_ends[i])
                ex.frame = Frame[i]
                exons.append(ex)

        tm = TranscriptModel()
        tm.gene = gene
        tm.trID = trName
        tm.trOrigId = trId
        tm.chr = chrom
        tm.strand = strand
        tm.tx = (transcription_start + 1, int(transcription_end))
        tm.cds = (int(cds_start) + 1, int(cds_end))
        tm.exons = exons
        tm.attr = OrderedDict()

        try:
            tm.attr["exonCount"] = exon_count
        except Exception:
            pass

        try:
            tm.attr["bin"] = bin
        except Exception:
            pass

        try:
            tm.attr["cdsStartStat"] = cdsStartStatus
        except Exception:
            pass

        try:
            tm.attr["cdsEndStat"] = cdsEndStatus
        except Exception:
            pass

        try:
            tm.attr["score"] = score
        except Exception:
            pass

        try:
            tm.attr["proteinID"] = proteinId
        except Exception:
            pass

        self.transcriptModels[tm.trID] = tm

        try:
            self._geneModels[gene].append(tm)
        except Exception:
            self._geneModels[gene] = [tm]

        try:
            self._utrModels[chrom][
                (transcription_start + 1, int(transcription_end))
            ].append(tm)
        except KeyError:
            # if e.args[0] == chrom:
            #     self._utrModels[chrom] = OrderedDict()
            self._utrModels[chrom] = OrderedDict()
            self._utrModels[chrom][
                (transcription_start + 1, int(transcription_end))
            ] = [tm]

        return -1

    def _create_gene_model_dict(self, location=None, gene_mapping_file=None):
        self._Alternative_names = OrderedDict()
        if gene_mapping_file is not None:
            if gene_mapping_file.endswith(".gz"):
                dict_file = gzip.open(gene_mapping_file, "rt")
            else:
                dict_file = open(gene_mapping_file, "rt")
            dict_file.readline()
            self._Alternative_names = dict(
                [(line.split()[0], line.split()[1]) for line in dict_file]
            )
            dict_file.close()

        if location is None:
            location = self.location

        geneModelFile = gzip.open(location, "rt")

        for line in geneModelFile:
            if line[0] == "#":
                continue
            line = line.split()
            # chrom = line[1 + self._shift]
            self.__addToDict(line)

        geneModelFile.close()

    def save(self, outputFile, gzipped=True):
        if gzipped:
            f = gzip.open(outputFile + ".gz", "wt")
        else:
            f = open(outputFile, "wt")

        f.write(
            "\t".join(
                "chr trID trOrigId gene strand tsBeg txEnd cdsStart cdsEnd "
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
                tm.chr,
                tm.trID,
                tm.trOrigId,
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

    def load(self, inFile):
        self.location = inFile
        f = gzip.open(inFile, mode="rt")
        line = f.readline()
        cs = line[:-1].split("\t")

        if len(cs) == 13:

            def parse_line(cs):
                assert len(cs) == 13
                return cs

        elif len(cs) == 12:

            def parse_line(cs):
                line = cs[:]
                line.insert(2, cs[1])
                assert len(line) == 13
                return line

        else:
            raise ValueError("unxpected gene model format")

        for line in f:
            line = str(line)
            cs = line[:-1].split("\t")
            (
                chrom,
                trID,
                trOrigId,
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
            ) = parse_line(cs)

            exons = []
            for frm, sr, sp in zip(
                *[x.split(",") for x in [eFrames, eStarts, eEnds]]
            ):
                e = Exon()
                e.frame = int(frm)
                e.start = int(sr)
                e.stop = int(sp)
                exons.append(e)

            attrs = dict([a.split(":") for a in add_attrs.split(";")])

            tm = TranscriptModel()
            tm.gene = gene
            tm.trID = trID
            tm.trOrigId = trOrigId
            tm.chr = chrom
            tm.strand = strand
            tm.tx = (int(txB), int(txE))
            tm.cds = (int(cdsB), int(cdsE))
            tm.exons = exons
            tm.attr = attrs

            self.transcriptModels[tm.trID] = tm
        f.close()
        self._updateIndexes()

    def _updateIndexes(self):
        self._geneModels = OrderedDict()
        self._utrModels = OrderedDict()
        for tm in list(self.transcriptModels.values()):
            if tm.gene not in self._geneModels:
                self._geneModels[tm.gene] = []
            self._geneModels[tm.gene].append(tm)
            if tm.chr not in self._utrModels:
                self._utrModels[tm.chr] = OrderedDict()
            if tm.tx not in self._utrModels[tm.chr]:
                self._utrModels[tm.chr][tm.tx] = []
            self._utrModels[tm.chr][tm.tx].append(tm)

    def gene_names(self):

        if self._geneModels is None:
            print(
                "Gene Models haven't been created/uploaded yet! "
                "Use either loadGeneModels function or "
                "self.createGeneModelDict function"
            )
            return None
        return list(self._geneModels.keys())

    def transcript_IDs(self):
        if self.transcriptModels is None:
            print(
                "Gene Models haven't been created/uploaded yet! "
                "Use either loadGeneModels function or "
                "self.createGeneModelDict function"
            )
            return None

        return list(self.transcriptModels.keys())

    def gene_models_by_gene_name(self, name):
        try:
            return self._geneModels[name]
        except Exception:
            pass

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

    def relabel_chromosomes(
        self, file="/data/unsafe/autism/genomes/hg19/ucsc2gatk.txt"
    ):

        if self.transcriptModels is None:
            print(
                "Gene Models haven't been created/uploaded yet! "
                "Use either loadGeneModels function or "
                "self.createGeneModelDict function"
            )
            return None

        f = open(file)
        Relabel = dict([(line.split()[0], line.split()[1]) for line in f])
        f.close()

        for chrom in list(self._utrModels.keys()):

            try:
                self._utrModels[Relabel[chrom]] = self._utrModels[chrom]
                self._utrModels.pop(chrom)
            except KeyError:
                self._utrModels.pop(chrom)

        # the b37 reference genome does not contain alternative haplotypes,
        # while hg19 does, so
        # these transcripts must be removed to be used with GenomeAccess,
        # which uses b37 as a reference

        transcriptsToDelete = []
        for trID in self.transcriptModels:
            try:
                self.transcriptModels[trID].chr = Relabel[
                    self.transcriptModels[trID].chr
                ]
            except KeyError:
                transcriptsToDelete.append(trID)

        for key in transcriptsToDelete:
            del self.transcriptModels[key]


class RefSeq(GeneModels):
    def __init__(self):
        super(RefSeq, self).__init__()

        self.name = "refseq"
        self.location = (
            "/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz"
        )
        self._shift = 1
        self._Alternative_names = None


class KnownGene(GeneModels):
    def __init__(self):
        super(KnownGene, self).__init__()

        self.name = "knowngene"
        self.location = (
            "/data/unsafe/autism/genomes/hg19/geneModels/knownGene.txt.gz"
        )
        self._shift = 0
        self._Alternative_names = None


class Ccds(GeneModels):
    def __init__(self):
        super(Ccds, self).__init__()
        self.name = "ccds"
        self.location = (
            "/data/unsafe/autism/genomes/hg19/geneModels/ccdsGene.txt.gz"
        )
        self._shift = 1
        self._Alternative_names = None


class MitoModel(GeneModels):
    def __init__(self):
        super(MitoModel, self).__init__()
        self.name = "mitomap"
        self.location = (
            "/data/unsafe/autism/genomes/hg19/geneModels/mitomap.txt"
        )
        self._Alternative_names = None

    def _create_gene_model_dict(self, file_name):

        self._utrModels["chrM"] = OrderedDict()
        if file_name is None:
            file = open(self.location)
        else:
            file = open(file_name)

        for line in file:
            line = line.split()
            if line[0] == "#":
                mode = line[1]
                continue
            if mode == "cds":
                mm = TranscriptModel()
                mm.gene = mm.trID = line[0]
                mm.strand = line[1]
                mm.cds = (int(line[2]), int(line[3]))
                mm.tx = (int(line[2]), int(line[3]))
                mm.chr = "chrM"
                mm.attr = {}
                e = Exon()
                e.start = int(line[2])
                e.stop = int(line[3])
                e.frame = 0
                mm.exons = [e]
                self._utrModels["chrM"][mm.tx] = [mm]
                self.transcriptModels[mm.trID] = mm
                self._geneModels[mm.gene] = [mm]

            elif mode == "rRNAs":
                mm = TranscriptModel()
                mm.gene = mm.trID = line[0]
                mm.strand = line[1]
                mm.cds = (int(line[2]), int(line[2]))
                mm.tx = (int(line[2]), int(line[3]))
                mm.chr = "chrM"
                mm.attr = {}
                e = Exon()
                e.start = int(line[2])
                e.stop = int(line[3])
                e.frame = -1
                mm.exons = [e]
                self._utrModels["chrM"][mm.tx] = [mm]
                self.transcriptModels[mm.trID] = mm
                self._geneModels[mm.gene] = [mm]

            elif mode == "tRNAs":
                mm = TranscriptModel()
                mm.chr = "chrM"
                mm.gene = mm.trID = line[0]
                mm.strand = line[1]
                mm.cds = (int(line[2]), int(line[2]))
                mm.tx = (int(line[2]), int(line[3]))
                mm.attr = {}
                mm.attr["anticodonB"] = line[4]
                mm.attr["anticodonE"] = line[5]
                e = Exon()
                e.start = int(line[2])
                e.stop = int(line[3])
                e.frame = -1
                mm.exons = [e]
                self._utrModels["chrM"][mm.tx] = [mm]
                self.transcriptModels[mm.trID] = mm
                self._geneModels[mm.gene] = [mm]

            else:
                continue
        file.close()


def save_pickled_dicts(gm, outputFile="./geneModels"):
    pickle.dump(
        [gm._utrModels, gm.transcriptModels, gm._geneModels],
        open(outputFile + ".dump", "wb"),
        protocol=2,
    )


def load_pickled_dicts(inputFile):
    gm = GeneModels()
    gm.location = inputFile
    pkl_file = open(inputFile, "rb")
    gm._utrModels, gm.transcriptModels, gm._geneModels = pickle.load(pkl_file)
    pkl_file.close()
    return gm


def create_region(chrom, b, e):
    reg = namedtuple("reg", "start stop chr")
    return reg(chr=chrom, start=b, stop=e)


def join_gene_models(*gene_models):

    if len(gene_models) < 2:
        raise Exception("The function needs at least 2 arguments!")

    gm = GeneModels()
    gm._utrModels = OrderedDict()
    gm._geneModels = OrderedDict()

    gm.transcriptModels = gene_models[0].transcriptModels.copy()

    for i in gene_models[1:]:
        gm.transcriptModels.update(i.transcriptModels)

    gm._updateIndexes()

    return gm


def get_gene_regions(GMs, autosomes=False, basic23=False):

    if autosomes or basic23:
        goodChr = [str(i) for i in range(1, 23)]
        if basic23:
            goodChr.append("X")
            goodChr.append("Y")

    genes = defaultdict(lambda _: defaultdict(list))
    for gm in list(GMs.transcriptModels.values()):
        if autosomes or basic23:
            if gm.chr in goodChr:
                genes[gm.gene][gm.chr] += gm.CDS_regions()
        else:
            genes[gm.gene][gm.chr] += gm.CDS_regions()

    rgnTpls = []

    for gnm, chrsD in list(genes.items()):
        for chr, rgns in list(chrsD.items()):

            clpsRgns = collapse_noChr(rgns)
            for rgn in sorted(clpsRgns, key=lambda x: x.start):
                rgnTpls.append((chr, rgn.start, rgn.stop, gnm))

    geneRgns = [rgnTpl for rgnTpl in sorted(rgnTpls)]

    return geneRgns


def load_gene_models(
    file_name="/data/unsafe/autism/genomes/hg19/geneModels/refGene.txt.gz",
    gene_mapping_file="default",
    format=None,
):

    if not format:
        if file_name.endswith("refGene.txt.gz"):
            format = "refseq"
        # elif file_name.endswith("ccdsGene.txt.gz"):
        #     format = 'ccds'
        # elif file_name.endswith("knownGene.txt.gz"):
        #     format = 'knowngene'
        # elif file_name.endswith(".dump"):
        #     format = 'pickled'
        # elif file_name.endswith("mitomap.txt"):
        #     format = 'mito'
        else:
            format = "default"

    if format.lower() == "refseq":
        gm = RefSeq()
        gm._utrModels = OrderedDict()
        gm.transcriptModels = OrderedDict()
        gm._geneModels = OrderedDict()
        if gene_mapping_file == "default":
            gene_mapping_file = None
        gm.location = file_name
        gm._create_gene_model_dict(file_name, gene_mapping_file)
    # elif format.lower() == "ccds":
    #     gm = Ccds()
    #     gm._utrModels = OrderedDict()
    #     gm.transcriptModels = OrderedDict()
    #     gm._geneModels = OrderedDict()
    #     if gene_mapping_file == "default":
    #         gene_mapping_file = os.path.dirname(file_name) + \
    #             "/ccdsId2Sym.txt.gz"
    #     gm.location = file_name
    #     gm._create_gene_model_dict(file_name, gene_mapping_file)
    # elif format.lower() == "knowngene":
    #     gm = KnownGene()
    #     gm._utrModels = OrderedDict()
    #     gm.transcriptModels = OrderedDict()
    #     gm._geneModels = OrderedDict()
    #     if gene_mapping_file == "default":
    #         gene_mapping_file = os.path.dirname(file_name) + \
    #               "/kgId2Sym.txt.gz"
    #     gm.location = file_name
    #     gm._create_gene_model_dict(file_name, gene_mapping_file)
    # elif format.lower() == "pickled":
    #     return(load_pickled_dicts(file_name))
    # elif format.lower() == "mito":
    #     gm = MitoModel()
    #     gm._create_gene_model_dict(file_name)
    elif format.lower() == "default":
        gm = GeneModels()
        gm.load(file_name)
    else:
        print(
            "Unrecognizable format! Choose between: "
            "'refseq', 'ccds', 'knowngene', 'pickled', 'mito' or 'default'"
        )
        sys.exit(-1098)

    return gm
