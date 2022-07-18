from __future__ import annotations

import os
import gzip
import logging
import copy

from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Optional, Dict, TextIO, cast

import pandas as pd

from dae.utils.regions import Region
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.fsspec_protocol import build_local_resource

logger = logging.getLogger(__name__)

# TODO IVAN: not all parsers handle the gene_mapping properly!


class Exon:
    """Provides exon model."""

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
    """Provides transcript model."""

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
        attributes=None,
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

        # it can be derivable from cds' start and end
        self._is_coding = is_coding

        self.attributes = attributes if attributes is not None else {}

    def is_coding(self):
        if self.cds[0] >= self.cds[1]:
            return False
        return True

    def CDS_regions(self, ss=0):
        """Compute CDS regions."""
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

            for exon in self.exons[k:]:
                utr3_regions.append(
                    Region(chrom=self.chrom, start=exon.start, stop=exon.stop)
                )

        return utr3_regions

    def all_regions(self, ss=0, prom=0):
        all_regions = []

        if ss == 0:
            for exon in self.exons:
                all_regions.append(
                    Region(chrom=self.chrom, start=exon.start, stop=exon.stop)
                )

        else:
            for exon in self.exons:
                if exon.stop <= self.cds[0]:
                    all_regions.append(
                        Region(
                            chrom=self.chrom,
                            start=exon.start, stop=exon.stop)
                    )
                elif exon.start <= self.cds[0]:
                    if exon.stop >= self.cds[1]:
                        all_regions.append(
                            Region(
                                chrom=self.chrom,
                                start=exon.start, stop=exon.stop)
                        )
                    else:
                        all_regions.append(
                            Region(
                                chrom=self.chrom,
                                start=exon.start,
                                stop=exon.stop + ss,
                            )
                        )
                elif exon.start > self.cds[1]:
                    all_regions.append(
                        Region(
                            chrom=self.chrom, start=exon.start, stop=exon.stop)
                    )
                else:
                    if exon.stop >= self.cds[1]:
                        all_regions.append(
                            Region(
                                chrom=self.chrom,
                                start=exon.start - ss,
                                stop=exon.stop,
                            )
                        )
                    else:
                        all_regions.append(
                            Region(
                                chrom=self.chrom,
                                start=exon.start - ss,
                                stop=exon.stop + ss,
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
        """Calculate codon frames."""
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
        """Update codon frames."""
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
class GeneModels:
    def __init__(self, resource: GenomicResource):
        self.resource = resource
        self.gene_models = None
        self.utr_models = None
        self.transcript_models: Dict[str, Any] = {}
        self.alternative_names: Dict[str, Any] = {}

        self._reset()

    def _reset(self):
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

    def update_indexes(self):
        self.gene_models = defaultdict(list)
        self.utr_models = defaultdict(lambda: defaultdict(list))
        for transcript in self.transcript_models.values():
            self.gene_models[transcript.gene].append(transcript)
            self.utr_models[transcript.chrom][transcript.tx].append(transcript)

    def gene_names(self):
        if self.gene_models is None:
            logger.warning(
                "gene models %s are empty", self.resource.resource_id)
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
            line = cast(dict, line)
            exon_starts = list(map(int, line["exonStarts"].split(",")))
            exon_ends = list(map(int, line["exonEnds"].split(",")))
            exon_frames = list(map(int, line["exonFrames"].split(",")))
            assert len(exon_starts) == len(exon_ends) == len(exon_frames)

            exons = []
            for start, end, frame in zip(exon_starts, exon_ends, exon_frames):
                exons.append(Exon(start=start, stop=end, frame=frame))
            attributes: dict = {}
            atts = line.get("atts")
            if atts and isinstance(atts, str):
                astep = [a.split(":") for a in atts.split(";")]
                attributes = dict([
                    (a[0], a[1]) for a in astep
                ])
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

        self.update_indexes()
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

        transcript_ids_counter: Dict[str, int] = defaultdict(int)

        for rec in records:
            gene = rec["#geneName"]
            if gene_mapping:
                gene = gene_mapping.get(gene, gene)
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

        transcript_ids_counter: Dict[str, int] = defaultdict(int)

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

        transcript_ids_counter: Dict[str, int] = defaultdict(int)
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
            return False

        records = df.to_dict(orient="records")

        transcript_ids_counter: Dict[str, int] = defaultdict(int)
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
        self, infile: TextIO,
        gene_mapping: Optional[Dict[str, str]] = None,
        nrows: Optional[int] = None
    ) -> bool:
        """Parse UCSC gene prediction models file fomrat.

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
                return False

        records = df.to_dict(orient="records")

        transcript_ids_counter: Dict[str, int] = defaultdict(int)
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
                return False

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
            tm.exons = sorted(tm.exons, key=lambda x: x.start)  # type: ignore
            tm.utrs = sorted(tm.utrs, key=lambda x: x[0])  # type: ignore
            tm.update_frames()

        return True

    @classmethod
    def _gene_mapping(cls, filename: str) -> Dict[str, str]:
        """Load alternative names for genes.

        Assume that its first line has two column names
        """
        df = pd.read_csv(filename, sep="\t")
        assert len(df.columns) == 2

        df = df.rename(columns={df.columns[0]: "tr_id", df.columns[1]: "gene"})

        records = df.to_dict(orient="records")

        alt_names = {}
        for rec in records:
            rec = cast(dict, rec)
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
        logger.info("going to infer gene models file format...")

        inferred_formats = []
        for fileformat in self.SUPPORTED_GENE_MODELS_FILE_FORMATS:
            parser = self._get_parser(fileformat)
            if parser is None:
                continue
            try:
                logger.debug("trying file format: %s...", fileformat)
                self._reset()
                infile.seek(0)
                res = parser(infile, nrows=50)
                if res:
                    inferred_formats.append(fileformat)
                    logger.debug(
                        "gene models format %s matches input", fileformat)
            except Exception as ex:
                logger.warning(
                    "file format %s does not match; %s",
                    fileformat, ex, exc_info=True)

        logger.info("inferred file formats: %s", inferred_formats)
        if len(inferred_formats) == 1:
            return inferred_formats[0]

        logger.error(
            "can't find gene model parser; "
            "inferred file formats are %s", inferred_formats)
        return None

    def load(self) -> GeneModels:
        """Load gene models."""
        filename = self.resource.get_config()["filename"]
        fileformat = self.resource.get_config().get("format", None)
        gene_mapping_filename = self.resource.get_config().get(
            "gene_mapping", None)
        logger.debug("loading gene models %s (%s)", filename, fileformat)
        compression = False
        if filename.endswith(".gz"):
            compression = True
        with self.resource.open_raw_file(
                filename, mode="rt", compression=compression) as infile:

            if fileformat is None:
                fileformat = self._infer_gene_model_parser(infile)
                logger.info("infering gene models file format: %s", fileformat)
                if fileformat is None:
                    logger.error(
                        "can't infer gene models file format for "
                        "%s...", self.resource.resource_id)
                    raise ValueError("can't infer gene models file format")

            parser = self._get_parser(fileformat)
            if parser is None:
                logger.error(
                    "Unsupported file format %s for "
                    "gene model file %s.", fileformat,
                    self.resource.resource_id)
                raise ValueError()

            gene_mapping = None
            if gene_mapping_filename is not None:
                compression = False
                if gene_mapping_filename.endswith(".gz"):
                    compression = True
                with self.resource.open_raw_file(
                        gene_mapping_filename, "rt",
                        compression=compression) as gene_mapping_file:
                    logger.debug(
                        "loading gene mapping from %s", gene_mapping_filename)
                    gene_mapping = self._gene_mapping(gene_mapping_file)

            infile.seek(0)
            self._reset()

            parser(infile, gene_mapping=gene_mapping)
        return self


def join_gene_models(*gene_models):

    if len(gene_models) < 2:
        raise ValueError("The function needs at least 2 arguments!")

    gm = GeneModels(gene_models[0].resource)
    gm.utr_models = {}
    gm.gene_models = {}

    gm.transcript_models = gene_models[0].transcript_models.copy()

    for i in gene_models[1:]:
        gm.transcript_models.update(i.transcript_models)

    gm.update_indexes()

    return gm


def build_gene_models_from_file(
    filename: str,
    fileformat: Optional[str] = None,
    gene_mapping_filename: Optional[str] = None
) -> GeneModels:
    """Load gene models from local filesystem."""
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    config = {
        "type": "gene_models",
        "filename": basename,
    }
    if fileformat:
        config["format"] = fileformat
    if gene_mapping_filename:
        gene_mapping = os.path.relpath(gene_mapping_filename, dirname)
        config["gene_mapping"] = gene_mapping

    res = build_local_resource(dirname, config)
    return build_gene_models_from_resource(res)


def build_gene_models_from_resource(
        resource: Optional[GenomicResource]) -> GeneModels:
    """Load gene models from a genomic resource."""
    if resource is None:
        raise ValueError(f"missing resource {resource}")

    if resource.get_type() != "gene_models":
        logger.error(
            "trying to open a resource %s of type "
            "%s as gene models", resource.resource_id, resource.get_type())
        raise ValueError(f"wrong resource type: {resource.resource_id}")

    gene_models = GeneModels(resource)
    gene_models.load()

    return gene_models
