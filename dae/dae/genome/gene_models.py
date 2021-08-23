from __future__ import annotations

import gzip
import os
import logging
import copy
import abc

from collections import defaultdict
from contextlib import contextmanager

import pandas as pd

from typing import Optional, Dict, TextIO

from dae.utils.regions import Region


logger = logging.getLogger(__name__)


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

    def __repr__(self):
        return (
            f"Exon(start={self.start}; stop={self.stop}; "
            f"number={self.number})"
        )


class TranscriptModel:
    def __init__(
        self,
        gene=None,
        tr_id=None,
        tr_name=None,
        chrom=None,
        strand=None,
        tx=None,
        cds=None,
        exons=None,
        start_codon=None,
        stop_codon=None,
        is_coding=False,
        attributes={},
    ):
        self.gene = gene
        self.tr_id = tr_id
        self.tr_name = tr_name
        self.chrom = chrom
        self.strand = strand
        self.tx = tx
        self.cds = cds
        self.exons = exons if exons is not None else []

        # for GTF
        self.utrs = []
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


@contextmanager
def _open_file(filename):
    if filename.endswith(".gz") or filename.endswith(".bgz"):
        infile = gzip.open(filename, "rt")
    else:
        infile = open(filename)
    try:
        yield infile
    finally:
        infile.close()


#
# GeneModel's
#
class GeneModelsBase:
    def __init__(self, name=None):
        self.name = name
        self._shift = None
        self.alternative_names = None

        self.utr_models = defaultdict(lambda: defaultdict(list))
        self.transcript_models = {}
        self.gene_models = defaultdict(list)

    def reset(self):
        self._shift = None
        self.alternative_names = None

        self.utr_models = defaultdict(lambda: defaultdict(list))
        self.transcript_models = {}
        self.gene_models = defaultdict(list)

    def _add_transcript_model(self, tm):

        assert tm.tr_id not in self.transcript_models

        self.transcript_models[tm.tr_id] = tm
        self.gene_models[tm.gene].append(tm)

        self.utr_models[tm.chrom][tm.tx].append(tm)

    def _update_indexes(self):
        self.gene_models = defaultdict(list)
        self.utr_models = defaultdict(lambda: defaultdict(list))
        for tm in self.transcript_models.values():
            self.gene_models[tm.gene].append(tm)
            self.utr_models[tm.chrom][tm.tx].append(tm)

    @abc.abstractmethod
    def open(self):
        pass

    def gene_names(self):
        if self.gene_models is None:
            logger.warning(f"gene models {self.name} are empty")
            return None

        return list(self.gene_models.keys())

    def gene_models_by_gene_name(self, name):
        return self.gene_models.get(name, None)

    # def gene_models_by_location(self, chrom, pos1, pos2=None):
    #     result = []

    #     if pos2 is None:
    #         for key in self.utr_models[chrom]:
    #             if pos1 >= key[0] and pos1 <= key[1]:
    #                 result.extend(self.utr_models[chrom][key])

    #     else:
    #         if pos2 < pos1:
    #             pos1, pos2 = pos2, pos1

    #         for key in self.utr_models[chrom]:
    #             if (pos1 <= key[0] and pos2 >= key[0]) or (
    #                 pos1 >= key[0] and pos1 <= key[1]
    #             ):
    #                 result.extend(self.utr_models[chrom][key])

    #     return result

    def relabel_chromosomes(self, relabel=None, map_file=None):
        assert relabel or map_file
        if not relabel:
            with open(map_file) as f:
                relabel = dict([line.strip("\n\r").split()[:2] for line in f])

        self.utr_models = {
            relabel[chrom]: v
            for chrom, v in self.utr_models.items()
            if chrom in relabel
        }

        self.transcript_models = {
            tid: tm
            for tid, tm in self.transcript_models.items()
            if tm.chrom in relabel
        }

        for tm in self.transcript_models.values():
            tm.chrom = relabel[tm.chrom]

    def _save_gene_models(self, outfile):
        outfile.write(
            "\t".join(
                [
                    "chr",
                    "trID",
                    "trOrigId",
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
            )
        )
        outfile.write("\n")

        for tm in self.transcript_models.values():
            exon_starts = ",".join([str(e.start) for e in tm.exons])
            exon_ends = ",".join([str(e.stop) for e in tm.exons])
            exon_frames = ",".join([str(e.frame) for e in tm.exons])

            add_atts = ";".join(
                [
                    k + ":" + str(v).replace(":", "_")
                    for k, v in list(tm.attributes.items())
                ]
            )

            cs = [
                tm.chrom,
                tm.tr_id,
                tm.tr_name,
                tm.gene,
                tm.strand,
                tm.tx[0],
                tm.tx[1],
                tm.cds[0],
                tm.cds[1],
                exon_starts,
                exon_ends,
                exon_frames,
                add_atts,
            ]
            outfile.write("\t".join([str(x) if x else "" for x in cs]))
            outfile.write("\n")

    def save(self, output_filename, gzipped=True):
        if gzipped:
            if not output_filename.endswith(".gz"):
                output_filename = f"{output_filename}.gz"
            with gzip.open(output_filename, "wt") as outfile:
                self._save_gene_models(outfile)
        else:

            with open(output_filename, "wt") as outfile:
                self._save_gene_models(outfile)

    def _parse_default_gene_models_format(
        self, infile: TextIO,
        gene_mapping: Optional[Dict[str, str]] = None,
        nrows: Optional[int] = None
    ) -> bool:

        infile.seek(0)
        df = pd.read_csv(
            infile,
            sep="\t",
            nrows=nrows,
            dtype={
                "chr": str,
                "trID": str,
                "trOrigId": str,
                "gene": str,
                "strand": str,
                "atts": str,
            },
        )

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

        if not set(expected_columns) <= set(df.columns):
            return False

        if "trOrigId" not in df.columns:
            tr_names = pd.Series(data=df["trID"].values)
            df["trOrigId"] = tr_names

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
            atts = line.get("atts")
            if atts and isinstance(atts, str):
                attributes = dict(
                    [a.split(":") for a in line.get("atts").split(";")]
                )
            tm = TranscriptModel(
                gene=line["gene"],
                tr_id=line["trID"],
                tr_name=line["trOrigId"],
                chrom=line["chr"],
                strand=line["strand"],
                tx=(line["tsBeg"], line["txEnd"]),
                cds=(line["cdsStart"], line["cdsEnd"]),
                exons=exons,
                attributes=attributes,
            )
            self.transcript_models[tm.tr_id] = tm

        self._update_indexes()
        if nrows is not None:
            return True

        return True

    def _parse_ref_flat_gene_models_format(
        self, infile: TextIO,
        gene_mapping: Optional[Dict[str, str]] = None,
        nrows: Optional[int] = None
    ) -> bool:
        expected_columns = [
            "#geneName",
            "name",
            "chrom",
            "strand",
            "txStart",
            "txEnd",
            "cdsStart",
            "cdsEnd",
            "exonCount",
            "exonStarts",
            "exonEnds",
        ]

        infile.seek(0)
        df = self._parse_raw(infile, expected_columns, nrows=nrows)
        if df is None:
            return False

        records = df.to_dict(orient="records")

        transcript_ids_counter = defaultdict(int)

        for rec in records:
            gene = rec["#geneName"]
            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (int(rec["txStart"]) + 1, int(rec["txEnd"]))
            cds = (int(rec["cdsStart"]) + 1, int(rec["cdsEnd"]))

            exon_starts = list(map(
                int, rec["exonStarts"].strip(",").split(",")))
            exon_ends = list(map(
                int, rec["exonEnds"].strip(",").split(",")))
            assert len(exon_starts) == len(exon_ends)

            exons = [
                Exon(start + 1, end)
                for start, end in zip(exon_starts, exon_ends)
            ]

            transcript_ids_counter[tr_name] += 1
            tr_id = f"{tr_name}_{transcript_ids_counter[tr_name]}"

            tm = TranscriptModel(
                gene=gene,
                tr_id=tr_id,
                tr_name=tr_name,
                chrom=chrom,
                strand=strand,
                tx=tx,
                cds=cds,
                exons=exons,
            )
            tm.update_frames()
            self._add_transcript_model(tm)

        return True

    def _parse_ref_seq_gene_models_format(
        self, infile: TextIO,
        gene_mapping: Optional[Dict[str, str]] = None,
        nrows: Optional[int] = None
    ) -> bool:
        expected_columns = [
            "#bin",
            "name",
            "chrom",
            "strand",
            "txStart",
            "txEnd",
            "cdsStart",
            "cdsEnd",
            "exonCount",
            "exonStarts",
            "exonEnds",
            "score",
            "name2",
            "cdsStartStat",
            "cdsEndStat",
            "exonFrames",
        ]

        infile.seek(0)
        df = self._parse_raw(infile, expected_columns, nrows=nrows)
        if df is None:
            return False

        records = df.to_dict(orient="records")

        transcript_ids_counter = defaultdict(int)

        for rec in records:
            gene = rec["name2"]
            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (int(rec["txStart"]) + 1, int(rec["txEnd"]))
            cds = (int(rec["cdsStart"]) + 1, int(rec["cdsEnd"]))

            exon_starts = list(map(
                int, rec["exonStarts"].strip(",").split(",")))
            exon_ends = list(map(
                int, rec["exonEnds"].strip(",").split(",")))
            assert len(exon_starts) == len(exon_ends)

            exons = [
                Exon(start + 1, end)
                for start, end in zip(exon_starts, exon_ends)
            ]

            transcript_ids_counter[tr_name] += 1
            tr_id = f"{tr_name}_{transcript_ids_counter[tr_name]}"

            attributes = {
                k: rec[k]
                for k in [
                    "#bin",
                    "score",
                    "exonCount",
                    "cdsStartStat",
                    "cdsEndStat",
                    "exonFrames",
                ]
            }
            tm = TranscriptModel(
                gene=gene,
                tr_id=tr_id,
                tr_name=tr_name,
                chrom=chrom,
                strand=strand,
                tx=tx,
                cds=cds,
                exons=exons,
                attributes=attributes,
            )
            tm.update_frames()
            self._add_transcript_model(tm)

        return True

    @classmethod
    def _probe_header(cls, infile, expected_columns, comment=None):
        infile.seek(0)
        df = pd.read_csv(
            infile, sep="\t", nrows=1, header=None, comment=comment)
        return list(df.iloc[0, :]) == expected_columns

    @classmethod
    def _probe_columns(cls, infile, expected_columns, comment=None):
        infile.seek(0)
        df = pd.read_csv(
            infile, sep="\t", nrows=1, header=None, comment=comment)
        return list(df.columns) == list(range(0, len(expected_columns)))

    @classmethod
    def _parse_raw(cls, infile, expected_columns, nrows=None, comment=None):
        if cls._probe_header(infile, expected_columns, comment=comment):
            infile.seek(0)
            df = pd.read_csv(infile, sep="\t", nrows=nrows, comment=comment)
            assert list(df.columns) == expected_columns

            return df
        elif cls._probe_columns(infile, expected_columns, comment=comment):
            infile.seek(0)
            df = pd.read_csv(
                infile,
                sep="\t",
                nrows=nrows,
                header=None,
                names=expected_columns,
                comment=comment,
            )
            assert list(df.columns) == expected_columns
            return df

    def _parse_ccds_gene_models_format(
        self, infile: TextIO,
        gene_mapping: Optional[Dict[str, str]] = None,
        nrows: Optional[int] = None
    ) -> bool:
        expected_columns = [
            # CCDS is identical with RefSeq
            "#bin",
            "name",
            "chrom",
            "strand",
            "txStart",
            "txEnd",
            "cdsStart",
            "cdsEnd",
            "exonCount",
            "exonStarts",
            "exonEnds",
            "score",
            "name2",
            "cdsStartStat",
            "cdsEndStat",
            "exonFrames",
        ]

        infile.seek(0)
        df = self._parse_raw(infile, expected_columns, nrows=nrows)
        if df is None:
            return False

        records = df.to_dict(orient="records")

        transcript_ids_counter = defaultdict(int)
        self.alternative_names = {}
        if gene_mapping is not None:
            self.alternative_names = copy.deepcopy(gene_mapping)

        for rec in records:
            gene = rec["name"]
            gene = self.alternative_names.get(gene, gene)

            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (int(rec["txStart"]) + 1, int(rec["txEnd"]))
            cds = (int(rec["cdsStart"]) + 1, int(rec["cdsEnd"]))

            exon_starts = list(map(
                int, rec["exonStarts"].strip(",").split(",")))
            exon_ends = list(map(
                int, rec["exonEnds"].strip(",").split(",")))
            assert len(exon_starts) == len(exon_ends)

            exons = [
                Exon(start + 1, end)
                for start, end in zip(exon_starts, exon_ends)
            ]

            transcript_ids_counter[tr_name] += 1
            tr_id = f"{tr_name}_{transcript_ids_counter[tr_name]}"

            attributes = {
                k: rec[k]
                for k in [
                    "#bin",
                    "score",
                    "exonCount",
                    "cdsStartStat",
                    "cdsEndStat",
                    "exonFrames",
                ]
            }
            tm = TranscriptModel(
                gene=gene,
                tr_id=tr_id,
                tr_name=tr_name,
                chrom=chrom,
                strand=strand,
                tx=tx,
                cds=cds,
                exons=exons,
                attributes=attributes,
            )
            tm.update_frames()
            self._add_transcript_model(tm)

        return True

    def _parse_known_gene_models_format(
        self, infile: TextIO,
        gene_mapping: Optional[Dict[str, str]] = None,
        nrows: Optional[int] = None
    ) -> bool:

        expected_columns = [
            "name",
            "chrom",
            "strand",
            "txStart",
            "txEnd",
            "cdsStart",
            "cdsEnd",
            "exonCount",
            "exonStarts",
            "exonEnds",
            "proteinID",
            "alignID",
        ]

        infile.seek(0)
        df = self._parse_raw(infile, expected_columns, nrows=nrows)
        if df is None:
            return None

        records = df.to_dict(orient="records")

        transcript_ids_counter = defaultdict(int)
        self.alternative_names = {}
        if gene_mapping is not None:
            self.alternative_names = copy.deepcopy(gene_mapping)

        for rec in records:
            gene = rec["name"]
            gene = self.alternative_names.get(gene, gene)

            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (int(rec["txStart"]) + 1, int(rec["txEnd"]))
            cds = (int(rec["cdsStart"]) + 1, int(rec["cdsEnd"]))

            exon_starts = list(map(
                int, rec["exonStarts"].strip(",").split(",")))
            exon_ends = list(map(
                int, rec["exonEnds"].strip(",").split(",")))
            assert len(exon_starts) == len(exon_ends)

            exons = [
                Exon(start + 1, end)
                for start, end in zip(exon_starts, exon_ends)
            ]

            transcript_ids_counter[tr_name] += 1
            tr_id = f"{tr_name}_{transcript_ids_counter[tr_name]}"

            attributes = {k: rec[k] for k in ["proteinID", "alignID"]}
            tm = TranscriptModel(
                gene=gene,
                tr_id=tr_id,
                tr_name=tr_name,
                chrom=chrom,
                strand=strand,
                tx=tx,
                cds=cds,
                exons=exons,
                attributes=attributes,
            )
            tm.update_frames()
            self._add_transcript_model(tm)

        return True

    def _parse_ucscgenepred_models_format(
        self, infile: str,
        gene_mapping: Optional[Dict[str, str]] = None,
        nrows: Optional[int] = None
    ) -> bool:
        """
        table genePred
        "A gene prediction."
            (
            string  name;               "Name of gene"
            string  chrom;              "Chromosome name"
            char[1] strand;             "+ or - for strand"
            uint    txStart;            "Transcription start position"
            uint    txEnd;              "Transcription end position"
            uint    cdsStart;           "Coding region start"
            uint    cdsEnd;             "Coding region end"
            uint    exonCount;          "Number of exons"
            uint[exonCount] exonStarts; "Exon start positions"
            uint[exonCount] exonEnds;   "Exon end positions"
            )

        table genePredExt
        "A gene prediction with some additional info."
            (
            string name;        	"Name of gene (usually transcript_id from
                                     GTF)"
            string chrom;       	"Chromosome name"
            char[1] strand;     	"+ or - for strand"
            uint txStart;       	"Transcription start position"
            uint txEnd;         	"Transcription end position"
            uint cdsStart;      	"Coding region start"
            uint cdsEnd;        	"Coding region end"
            uint exonCount;     	"Number of exons"
            uint[exonCount] exonStarts; "Exon start positions"
            uint[exonCount] exonEnds;   "Exon end positions"
            int score;            	"Score"
            string name2;       	"Alternate name (e.g. gene_id from GTF)"
            string cdsStartStat; 	"Status of CDS start annotation (none,
                                        unknown, incomplete, or complete)"
            string cdsEndStat;   	"Status of CDS end annotation
                                        (none, unknown,
                                        incomplete, or complete)"
            lstring exonFrames; 	"Exon frame offsets {0,1,2}"
            )
        """

        expected_columns = [
            "name",
            "chrom",
            "strand",
            "txStart",
            "txEnd",
            "cdsStart",
            "cdsEnd",
            "exonCount",
            "exonStarts",
            "exonEnds",
            "score",
            "name2",
            "cdsStartStat",
            "cdsEndStat",
            "exonFrames",
        ]

        infile.seek(0)
        df = self._parse_raw(infile, expected_columns[:10], nrows=nrows)
        if df is None:
            infile.seek(0)
            df = self._parse_raw(infile, expected_columns, nrows=nrows)
            if df is None:
                return None

        records = df.to_dict(orient="records")

        transcript_ids_counter = defaultdict(int)
        self.alternative_names = {}
        if gene_mapping is not None:
            self.alternative_names = copy.deepcopy(gene_mapping)

        for rec in records:
            gene = rec.get("name2")
            if not gene:
                gene = rec["name"]
            gene = self.alternative_names.get(gene, gene)

            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (int(rec["txStart"]) + 1, int(rec["txEnd"]))
            cds = (int(rec["cdsStart"]) + 1, int(rec["cdsEnd"]))

            exon_starts = list(map(
                int, rec["exonStarts"].strip(",").split(",")))
            exon_ends = list(map(
                int, rec["exonEnds"].strip(",").split(",")))
            assert len(exon_starts) == len(exon_ends)

            exons = [
                Exon(start + 1, end)
                for start, end in zip(exon_starts, exon_ends)
            ]

            transcript_ids_counter[tr_name] += 1
            tr_id = f"{tr_name}_{transcript_ids_counter[tr_name]}"

            attributes = {}
            for attr in expected_columns[10:]:
                if attr in rec:
                    attributes[attr] = rec.get(attr)
            tm = TranscriptModel(
                gene=gene,
                tr_id=tr_id,
                tr_name=tr_name,
                chrom=chrom,
                strand=strand,
                tx=tx,
                cds=cds,
                exons=exons,
                attributes=attributes,
            )
            tm.update_frames()
            self._add_transcript_model(tm)

        return True

    def _parse_gtf_gene_models_format(
        self, infile: TextIO,
        gene_mapping: Optional[Dict[str, str]] = None,
        nrows: Optional[int] = None
    ) -> bool:

        expected_columns = [
            "seqname",
            "source",
            "feature",
            "start",
            "end",
            "score",
            "strand",
            "phase",
            "attributes",
            # "comments",
        ]

        infile.seek(0)
        df = self._parse_raw(
            infile, expected_columns, nrows=nrows, comment="#",)

        if df is None:
            expected_columns.append("comment")
            infile.seek(0)
            df = self._parse_raw(
                infile, expected_columns, nrows=nrows, comment="#")
            if df is None:
                return None

        def parse_gtf_attributes(attributes):
            attributes = list(
                filter(lambda x: x, [a.strip() for a in attributes.split(";")])
            )
            result = {}
            for attr in attributes:
                key, value = attr.split(" ")
                result[key.strip()] = value.strip('"').strip()
            return result

        records = df.to_dict(orient="records")
        for rec in records:
            feature = rec["feature"]
            if feature == "gene":
                continue
            attributes = parse_gtf_attributes(rec["attributes"])
            tr_id = attributes["transcript_id"]
            if feature in set(["transcript", "Selenocysteine"]):
                if feature == "Selenocysteine" and \
                        tr_id in self.transcript_models:
                    continue
                if tr_id in self.transcript_models:
                    raise ValueError(
                        f"{tr_id} of {feature} already in transcript models"
                    )
                tm = TranscriptModel(
                    gene=attributes["gene_name"],
                    tr_id=tr_id,
                    tr_name=tr_id,
                    chrom=rec["seqname"],
                    strand=rec["strand"],
                    tx=(rec["start"], rec["end"]),
                    cds=(rec["end"], rec["start"]),
                    attributes=attributes,
                )
                self._add_transcript_model(tm)
                continue
            if feature in {"CDS", "exon"}:
                if tr_id not in self.transcript_models:
                    raise ValueError(
                        f"exon or CDS transcript {tr_id} not found "
                        f"in transctipt models"
                    )
                exon_number = int(attributes["exon_number"])
                tm = self.transcript_models[tr_id]
                if len(tm.exons) < exon_number:
                    tm.exons.append(Exon())
                assert len(tm.exons) >= exon_number

                exon = tm.exons[exon_number - 1]
                if feature == "exon":
                    exon.start = rec["start"]
                    exon.stop = rec["end"]
                    exon.frame = -1
                    exon.number = exon_number
                    continue
                if feature == "CDS":
                    exon.cds_start = rec["start"]
                    exon.cds_stop = rec["end"]
                    exon.frame = rec["phase"]
                    tm._is_coding = True
                    continue
            if feature in {"UTR", "5UTR", "3UTR", "start_codon", "stop_codon"}:
                exon_number = int(attributes["exon_number"])
                tm = self.transcript_models[tr_id]

                if feature in {"UTR", "5UTR", "3UTR"}:
                    tm.utrs.append((rec["start"], rec["end"], exon_number))
                    continue
                if feature == "start_codon":
                    tm.start_codon = (rec["start"], rec["end"], exon_number)
                if feature == "stop_codon":
                    tm.stop_codon = (rec["start"], rec["end"], exon_number)
                cds = tm.cds
                tm.cds = (min(cds[0], rec["start"]), max(cds[1], rec["end"]))
                continue

            raise ValueError(
                f"unknown feature {feature} found in gtf gene models")

        for tm in self.transcript_models.values():
            tm.exons = sorted(tm.exons, key=lambda x: x.start)
            tm.utrs = sorted(tm.utrs, key=lambda x: x[0])
            tm.update_frames()

        return True

    @classmethod
    def _gene_mapping(cls, filename: str) -> Dict[str, str]:
        """
        alternative names for genes
        assume that its first line has two column names
    """

        df = pd.read_csv(filename, sep="\t")
        assert len(df.columns) == 2

        df = df.rename(columns={df.columns[0]: "tr_id", df.columns[1]: "gene"})

        records = df.to_dict(orient="records")

        alt_names = {}
        for rec in records:
            alt_names[rec["tr_id"]] = rec["gene"]

        return alt_names

    SUPPORTED_GENE_MODELS_FILE_FORMATS = {
        "default",
        "refflat",
        "refseq",
        "ccds",
        "knowngene",
        "gtf",
        "ucscgenepred",
    }

    def _get_parser(self, fileformat):
        if fileformat == "default":
            return self._parse_default_gene_models_format
        elif fileformat == "refflat":
            return self._parse_ref_flat_gene_models_format
        elif fileformat == "refseq":
            return self._parse_ref_seq_gene_models_format
        elif fileformat == "ccds":
            return self._parse_ccds_gene_models_format
        elif fileformat == "knowngene":
            return self._parse_known_gene_models_format
        elif fileformat == "gtf":
            return self._parse_gtf_gene_models_format
        elif fileformat == "ucscgenepred":
            return self._parse_ucscgenepred_models_format
        return None

    def _infer_gene_model_parser(self, infile, fileformat=None):

        parser = self._get_parser(fileformat)
        if parser is not None:
            return fileformat
        logger.warning("going to infer gene models file format...")

        inferred_formats = []
        for fileformat in self.SUPPORTED_GENE_MODELS_FILE_FORMATS:
            parser = self._get_parser(fileformat)
            if parser is None:
                continue
            try:
                logger.debug(f"trying file format: {fileformat}...")
                self.reset()
                infile.seek(0)
                res = parser(infile, nrows=50)
                if res:
                    inferred_formats.append(fileformat)
                    logger.debug(
                        f"gene models format {fileformat} matches input")
            except Exception as ex:
                logger.warning(
                    f"file format {fileformat} does not match; {ex}")
                pass

        logger.info(f"inferred file formats: {inferred_formats}")
        if len(inferred_formats) == 1:
            return inferred_formats[0]

        logger.error(
            f"can't find gene model parser; "
            f"inferred file formats are {inferred_formats}"
        )
        return None


class GeneModels(GeneModelsBase):

    def __init__(self, filename, gene_mapping_filename=None, fileformat=None):
        super(GeneModels, self).__init__(filename)
        self.filename = filename
        self.gene_mapping_filename = gene_mapping_filename
        self.fileformat = fileformat

    def open(self):
        assert os.path.exists(self.filename), self.filename
        logger.debug(f"loading gene models from {self.filename}")

        fileformat = self.fileformat
        with _open_file(self.filename) as infile:
            if self.fileformat is None:
                fileformat = self._infer_gene_model_parser(infile)
                logger.debug(f"infering gene models file format: {fileformat}")
                if fileformat is None:
                    logger.error(
                        f"can't infer gene models file format for "
                        f"{self.filename}...")
                    raise ValueError()

            parser = self._get_parser(fileformat)
            if parser is None:
                logger.error(
                    f"unsupported gene model file {self.filename} "
                    f"gene file format: {fileformat}")
                raise ValueError()

            gene_mapping = None
            if self.gene_mapping_filename is not None:
                assert os.path.exists(self.gene_mapping_filename)
                gene_mapping = self._gene_mapping(self.gene_mapping_filename)

            infile.seek(0)
            self.reset()

            print(parser, type(parser))
            parser(infile, gene_mapping=gene_mapping)


def load_gene_models(
    filename: str,
    gene_mapping_filename: Optional[str] = None,
    fileformat: Optional[str] = None
) -> GeneModels:

    gm = GeneModels(
        filename,
        gene_mapping_filename=gene_mapping_filename,
        fileformat=fileformat)
    try:
        gm.open()
        return gm
    except Exception:
        logger.exception(f"unable to load gene models from {filename}")
    return None


def join_gene_models(*gene_models):

    if len(gene_models) < 2:
        raise Exception("The function needs at least 2 arguments!")

    gm = GeneModelsBase()
    gm.utr_models = {}
    gm.gene_models = {}

    gm.transcript_models = gene_models[0].transcript_models.copy()

    for i in gene_models[1:]:
        gm.transcript_models.update(i.transcript_models)

    gm._update_indexes()

    return gm


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
    for _nLR, line in enumerate(f):

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

        gm.transcript_models[tm.tr_id] = tm

    f.close()
    gm._update_indexes()


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


def refSeqParser(gm, location=None, gene_mapping_file=None):
    colNames = Columns4FileFormat["refSeq"]
    lR = parserLine4UCSC_genePred(colNames)

    if not location:
        location = gm.location

    GMF = openFile(location)

    trIdC = defaultdict(int)
    for _nLR, line in enumerate(GMF):
        if line[0] == "#":
            continue

        tm, cs = lR.parse(line)
        tm.gene = cs["name2"]

        trIdC[tm.tr_id] += 1
        tm.tr_id += "_" + str(trIdC[tm.tr_id])
        tm.update_frames()

        gm._add_transcript_model(tm)

    GMF.close()


def refFlatParser(gm, file_name, gene_mapping_file="default"):
    assert gene_mapping_file == "default"

    # column names
    colNames = Columns4FileFormat["refFlat"]
    lR = parserLine4UCSC_genePred(colNames)

    GMF = openFile(file_name)

    trIdC = defaultdict(int)
    for _nLR, line in enumerate(GMF):
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

        gm._add_transcript_model(tm)

    GMF.close()


def knownGeneParser(gm, file_name, gene_mapping_file="default"):
    colNames = Columns4FileFormat["knownGene"]
    lR = parserLine4UCSC_genePred(colNames)

    if gene_mapping_file == "default":
        gene_mapping_file = os.path.join(
            os.path.dirname(file_name), "kg_id2sym.txt.gz"
        )

    gm.alternative_names = GeneModels._gene_mapping(gene_mapping_file)

    gmf = openFile(file_name)

    trIdC = defaultdict(int)
    for _nLR, line in enumerate(gmf):
        if line[0] == "#":
            continue

        tm, cs = lR.parse(line)
        try:
            tm.gene = gm.alternative_names[cs["name"]]
        except KeyError:
            tm.gene = cs["name"]

        trIdC[tm.tr_id] += 1
        tm.tr_id += "_" + str(trIdC[tm.tr_id])
        tm.update_frames()

        gm._add_transcript_model(tm)

    gmf.close()


#  format = refseq
#  CCC = {"refseq":refseqParser, ....}
#  o = GeneModelsBase()
#  CCC[format](o,file, geneMapFile)
#


# ccdsGene
def ccdsParser(gm, file_name, gene_mapping_file="default"):
    colNames = Columns4FileFormat["ccds"]
    lR = parserLine4UCSC_genePred(colNames)

    if gene_mapping_file == "default":
        gene_mapping_file = os.path.join(
            os.path.dirname(file_name), "ccds_id2sym.txt.gz"
        )

    gm.alternative_names = GeneModels._gene_mapping(gene_mapping_file)

    GMF = openFile(file_name)

    trIdC = defaultdict(int)
    for _nLR, line in enumerate(GMF):
        if line[0] == "#":
            continue

        tm, cs = lR.parse(line)
        tm.gene = gm.alternative_names.get(cs["name"])
        if tm.gene is None:
            tm.gene = cs["name"]

        trIdC[tm.tr_id] += 1
        tm.tr_id += "_" + str(trIdC[tm.tr_id])
        tm.update_frames()

        gm._add_transcript_model(tm)

    GMF.close()


def ucscGenePredParser(gm, file_name, gene_mapping_file="default"):
    colNames = Columns4FileFormat["ucscGenePred"]
    lR = parserLine4UCSC_genePred(colNames)

    if gene_mapping_file != "default":
        gm.alternative_names = GeneModels._gene_mapping(gene_mapping_file)

    GMF = openFile(file_name)

    trIdC = defaultdict(int)
    for _nLR, line in enumerate(GMF):
        if line[0] == "#":
            continue

        tm, cs = lR.parse(line)
        try:
            tm.gene = gm.alternative_names[cs["name"]]
        except (KeyError, TypeError):
            tm.gene = cs["name"]

        trIdC[tm.tr_id] += 1
        tm.tr_id += "_" + str(trIdC[tm.tr_id])
        tm.update_frames()

        gm._add_transcript_model(tm)

    GMF.close()


def gtfGeneModelParser(gm, file_name, gene_mapping_file=None):
    gm.name = "GTF"
    # print( 'GeneModel format: ', gm.name, '\timporting: ',
    # file_name, file=sys.stderr )
    gm.location = file_name

    f = GtfFileReader(file_name)
    for _nLR, rx in enumerate(f):
        if rx["feature"] in ["gene"]:
            continue

        # if 'transcript_support_level' in rx['attributes']  and
        # rx['attributes']['transcript_support_level'] != '1': continue

        trID = rx["attributes"]["transcript_id"]
        if rx["feature"] in ["transcript", "Selenocysteine"]:
            if (
                rx["feature"] in ["Selenocysteine"]
                and trID in gm.transcript_models
            ):
                continue

            if trID in gm.transcript_models:
                raise Exception(
                    "{} of {}: already existed on transcript_models".format(
                        trID, rx["feature"]
                    )
                )

            tm = TranscriptModel()
            tm.gene = rx["attributes"]["gene_name"]
            tm.tr_id = trID
            tm.tr_name = trID
            tm.chrom = rx["seqname"]
            tm.strand = rx["strand"]
            tm.tx = (rx["start"], rx["end"])
            tm.cds = (rx["end"], rx["start"])
            tm.attr = rx["attributes"]

            gm._add_transcript_model(tm)
            # gm.transcript_models[tm.tr_id] = tm
            continue

        if rx["feature"] in ["CDS", "exon"]:
            if trID not in gm.transcript_models:
                raise Exception(
                    "{}: exon or CDS not existed on transcript_models".format(
                        trID
                    )
                )

            ix = (
                int(rx["attributes"]["exon_number"]) - 1
            )  # 1-based to 0-based indexing
            # print trID, len(gm.transcript_models[trID].exons), ix,
            # rx['attributes']['exon_number']
            if len(gm.transcript_models[trID].exons) <= ix:
                gm.transcript_models[trID].exons.append(Exon())

            if rx["feature"] == "exon":
                gm.transcript_models[trID].exons[ix].start = rx["start"]
                gm.transcript_models[trID].exons[ix].stop = rx["end"]
                gm.transcript_models[trID].exons[ix].frame = -1
                gm.transcript_models[trID].exons[ix].number = (
                    ix + 1
                )  # return to 1-base indexing

                continue

            if rx["feature"] == "CDS":
                gm.transcript_models[trID].exons[ix].cds_start = rx["start"]
                gm.transcript_models[trID].exons[ix].cds_stop = rx["end"]
                gm.transcript_models[trID].exons[ix].frame = int(rx["phase"])

                gm.transcript_models[trID]._is_coding = True

                # cx = gm.transcript_models[trID].cds
                # gm.transcript_models[trID].cds =
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
                gm.transcript_models[trID].utrs.append(
                    (rx["start"], rx["end"], ix)
                )
                continue

            if rx["feature"] == "start_codon":
                gm.transcript_models[trID].start_codon = (
                    rx["start"],
                    rx["end"],
                    ix,
                )
            if rx["feature"] == "stop_codon":
                gm.transcript_models[trID].stop_codon = (
                    rx["start"],
                    rx["end"],
                    ix,
                )

            cx = gm.transcript_models[trID].cds
            gm.transcript_models[trID].cds = (
                min(cx[0], rx["start"]),
                max(cx[1], rx["end"]),
            )

            continue

        raise Exception("unknown {} found".format(rx["feature"]))

    for k in gm.transcript_models.keys():
        tm = gm.transcript_models[k]
        tm.exons = sorted(tm.exons, key=lambda x: x.start)
        tm.utrs = sorted(tm.utrs, key=lambda x: x[0])
        tm.update_frames()

    # TODO: no needed: done by gm._add_transcript_model(tm)
    # for k, gx in gm.transcript_models.items():
    #   gID = gx.gene
    #   if gID not in gm.gene_models: gm.gene_models[gID] = []
    #
    #   gm.gene_models[gID].append( gx )


#
#  MT chromosome
#
def mitoGeneModelParser(gm, file_name, gene_mapping_file=None):
    gm.name = "mitomap"
    gm.alternative_names = None

    gm.utr_models["chrM"] = {}
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

        gm.utr_models["chrM"][mm.tx] = [mm]
        gm.transcript_models[mm.tr_id] = mm
        gm.gene_models[mm.gene] = [mm]

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

        assert len(terms) == len(self.header), (self.header, terms)

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

        return tm, cs
