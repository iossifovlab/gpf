# pylint: disable=too-many-lines
from __future__ import annotations

import copy
import gzip
import logging
from collections import defaultdict
from datetime import datetime
from io import StringIO
from typing import IO, Any, ClassVar, Optional, Protocol, cast

import pandas as pd

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.fsspec_protocol import build_local_resource
from dae.genomic_resources.resource_implementation import (
    ResourceConfigValidationMixin,
    get_base_resource_schema,
)
from dae.utils.regions import BedRegion, Region, collapse

logger = logging.getLogger(__name__)


class Exon:
    """Provides exon model."""

    def __init__(
        self,
        start: int,
        stop: int,
        frame: Optional[int] = None,
    ):
        """Initialize exon model.

        Args:
            start: The genomic start position of the exon (1-based).
            stop (int): The genomic stop position of the exon (1-based, closed).
            frame (Optional[int]): The frame of the exon.
        """

        self.start = start
        self.stop = stop
        self.frame = frame  # related to cds

    def __repr__(self) -> str:
        return f"Exon(start={self.start}; stop={self.stop})"


class TranscriptModel:
    """Provides transcript model."""

    def __init__(
        self,
        gene: str,
        tr_id: str,
        tr_name: str,
        chrom: str,
        strand: str,
        tx: tuple[int, int],  # pylint: disable=invalid-name
        cds: tuple[int, int],
        exons: Optional[list[Exon]] = None,
        attributes: Optional[dict[str, Any]] = None,
    ):
        """Initialize transcript model.

        Args:
            gene (str): The gene name.
            tr_id (str): The transcript ID.
            tr_name (str): The transcript name.
            chrom (str): The chromosome name.
            strand (str): The strand of the transcript.
            tx (tuple[int, int]): The transcript start and end positions.
                (1-based, closed interval)
            cds (tuple[int, int]): The coding region start and end positions.
                The CDS region includes the start and stop codons.
                (1-based, closed interval)
            exons (Optional[list[Exon]]): The list of exons. Defaults to
                empty list.
            attributes (Optional[dict[str, Any]]): The additional attributes.
                Defaults to empty dictionary.
        """
        self.gene = gene
        self.tr_id = tr_id
        self.tr_name = tr_name
        self.chrom = chrom
        self.strand = strand
        self.tx = tx  # pylint: disable=invalid-name
        self.cds = cds
        self.exons: list[Exon] = exons if exons is not None else []
        self.attributes = attributes if attributes is not None else {}

    def is_coding(self) -> bool:
        return self.cds[0] < self.cds[1]

    def cds_regions(self, ss_extend: int = 0) -> list[BedRegion]:
        """Compute CDS regions."""
        if self.cds[0] >= self.cds[1]:
            return []

        regions = []
        k = 0
        while self.exons[k].stop < self.cds[0]:
            k += 1

        if self.cds[1] <= self.exons[k].stop:
            regions.append(
                BedRegion(
                    chrom=self.chrom, start=self.cds[0], stop=self.cds[1]),
            )
            return regions

        regions.append(
            BedRegion(
                chrom=self.chrom,
                start=self.cds[0],
                stop=self.exons[k].stop + ss_extend,
            ),
        )
        k += 1
        while k < len(self.exons) and self.exons[k].stop <= self.cds[1]:
            if self.exons[k].stop < self.cds[1]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start - ss_extend,
                        stop=self.exons[k].stop + ss_extend,
                    ),
                )
                k += 1
            else:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start - ss_extend,
                        stop=self.exons[k].stop,
                    ),
                )
                return regions

        if k < len(self.exons) and self.exons[k].start <= self.cds[1]:
            regions.append(
                BedRegion(
                    chrom=self.chrom,
                    start=self.exons[k].start - ss_extend,
                    stop=self.cds[1],
                ),
            )

        return regions

    def utr5_regions(self) -> list[BedRegion]:
        """Build list of UTR5 regions."""
        if self.cds[0] >= self.cds[1]:
            return []

        regions = []
        k = 0
        if self.strand == "+":
            while self.exons[k].stop < self.cds[0]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.exons[k].stop,
                    ),
                )
                k += 1
            if self.exons[k].start < self.cds[0]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.cds[0] - 1,
                    ),
                )

        else:
            while self.exons[k].stop < self.cds[1]:
                k += 1
            if self.exons[k].stop == self.cds[1]:
                k += 1
            else:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.cds[1] + 1,
                        stop=self.exons[k].stop,
                    ),
                )
                k += 1

            regions.extend([
                BedRegion(chrom=self.chrom, start=exon.start, stop=exon.stop)
                for exon in self.exons[k:]
            ])

        return regions

    def utr3_regions(self) -> list[BedRegion]:
        """Build and return list of UTR3 regions."""
        if self.cds[0] >= self.cds[1]:
            return []

        regions = []
        k = 0
        if self.strand == "-":
            while self.exons[k].stop < self.cds[0]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.exons[k].stop,
                    ),
                )
                k += 1
            if self.exons[k].start < self.cds[0]:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.exons[k].start,
                        stop=self.cds[0] - 1,
                    ),
                )

        else:
            while self.exons[k].stop < self.cds[1]:
                k += 1
            if self.exons[k].stop == self.cds[1]:
                k += 1
            else:
                regions.append(
                    BedRegion(
                        chrom=self.chrom,
                        start=self.cds[1] + 1,
                        stop=self.exons[k].stop,
                    ),
                )
                k += 1

            regions.extend([
                BedRegion(chrom=self.chrom, start=exon.start, stop=exon.stop)
                for exon in self.exons[k:]
            ])

        return regions

    def all_regions(
        self, ss_extend: int = 0, prom: int = 0,
    ) -> list[BedRegion]:
        """Build and return list of regions."""
        # pylint:disable=too-many-branches
        regions = []

        if ss_extend == 0:
            regions.extend([
                BedRegion(chrom=self.chrom, start=exon.start, stop=exon.stop)
                for exon in self.exons
            ])

        else:
            for exon in self.exons:
                if exon.stop <= self.cds[0]:
                    regions.append(
                        BedRegion(
                            chrom=self.chrom,
                            start=exon.start, stop=exon.stop),
                    )
                elif exon.start <= self.cds[0]:
                    if exon.stop >= self.cds[1]:
                        regions.append(
                            BedRegion(
                                chrom=self.chrom,
                                start=exon.start, stop=exon.stop),
                        )
                    else:
                        regions.append(
                            BedRegion(
                                chrom=self.chrom,
                                start=exon.start,
                                stop=exon.stop + ss_extend,
                            ),
                        )
                elif exon.start > self.cds[1]:
                    regions.append(
                        BedRegion(
                            chrom=self.chrom, start=exon.start, stop=exon.stop),
                    )
                else:
                    if exon.stop >= self.cds[1]:
                        regions.append(
                            BedRegion(
                                chrom=self.chrom,
                                start=exon.start - ss_extend,
                                stop=exon.stop,
                            ),
                        )
                    else:
                        regions.append(
                            BedRegion(
                                chrom=self.chrom,
                                start=exon.start - ss_extend,
                                stop=exon.stop + ss_extend,
                            ),
                        )

        if prom != 0:
            if self.strand == "+":
                regions[0] = BedRegion(
                    chrom=regions[0].chrom,
                    start=regions[0].start - prom,
                    stop=regions[0].stop,
                )
            else:
                regions[-1] = BedRegion(
                    chrom=regions[-1].chrom,
                    start=regions[-1].start,
                    stop=regions[-1].stop + prom,
                )

        return regions

    def total_len(self) -> int:
        length = 0
        for reg in self.exons:
            length += reg.stop - reg.start + 1
        return length

    def cds_len(self) -> int:
        regions = self.cds_regions()
        length = 0
        for reg in regions:
            length += reg.stop - reg.start + 1
        return length

    def utr3_len(self) -> int:
        utr3 = self.utr3_regions()
        length = 0
        for reg in utr3:
            length += reg.stop - reg.start + 1

        return length

    def utr5_len(self) -> int:
        utr5 = self.utr5_regions()
        length = 0
        for reg in utr5:
            length += reg.stop - reg.start + 1

        return length

    def calc_frames(self) -> list[int]:
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
                    (fms[k] + self.exons[k].stop - self.exons[k].start + 1) % 3,
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
                    % 3,
                )
                k -= 1
            fms += [-1] * (length - len(fms))
            fms = fms[::-1]

        assert len(self.exons) == len(fms)
        return fms

    def update_frames(self) -> None:
        """Update codon frames."""
        frames = self.calc_frames()
        for exon, frame in zip(self.exons, frames):
            exon.frame = frame

    def test_frames(self) -> bool:
        frames = self.calc_frames()
        for exon, frame in zip(self.exons, frames):
            if exon.frame != frame:
                return False
        return True

    def to_gtf(self) -> str:
        """Output a GTF format string representation."""
        buffer = StringIO()

        src = self.attributes.get("gene_source", ".")

        attributes = dict(self.attributes)
        if "gene_name" not in attributes:
            attributes["gene_name"] = self.gene
        if "gene_id" not in attributes:
            attributes["gene_id"] = self.gene
        str_attrs = ";".join(f'{k} "{v}"' for k, v in attributes.items())

        def calc_exon_number(start: int, stop: int) -> int:
            for exon_number, exon in enumerate(self.exons):
                if not (start > exon.stop or stop < exon.start):
                    return exon_number + 1 if self.strand == "+" \
                           else len(self.exons) - exon_number
            raise KeyError

        def write_record(
            feature: str,
            start: int, stop: int,
            *,
            write_exon_number: bool = False,
        ) -> None:
            buffer.write(f"{self.chrom}\t{src}\t")
            buffer.write(f"{feature}\t{start}\t{stop}\t.\t{self.strand}\t.\t")
            buffer.write(str_attrs)
            if write_exon_number:
                buffer.write(f';exon_number "{calc_exon_number(start, stop)}"')
            buffer.write(";\n")

        write_record("transcript", self.tx[0], self.tx[1])

        for exon in self.exons:
            write_record("exon", exon.start, exon.stop, write_exon_number=True)

        cds_regions = self.cds_regions()
        for cds in cds_regions[:-1]:  # all but last CDS region
            write_record("CDS", cds.start, cds.stop, write_exon_number=True)
        # handle last separately, because the GTF format
        # excludes the stop codon from the CDS regions
        write_record("CDS",
            cds_regions[-1].start,
            cds_regions[-1].stop - 2,
            write_exon_number=True)

        for utr in self.utr3_regions() + self.utr5_regions():
            write_record("UTR", utr.start, utr.stop)

        left = Region(self.chrom, self.cds[0], self.cds[0] + 2)
        right = Region(self.chrom, self.cds[1] - 2, self.cds[1])

        start_codon = left if self.strand == "+" else right
        stop_codon = right if self.strand == "+" else left

        write_record("start_codon",
                     start_codon.start, start_codon.stop,  # type: ignore
                     write_exon_number=True)
        write_record("stop_codon",
                      stop_codon.start, stop_codon.stop,  # type: ignore
                      write_exon_number=True)

        res = buffer.getvalue()
        buffer.close()
        return res


class GeneModelsParser(Protocol):
    """Gene models parser function type."""

    def __call__(
        self, infile: IO,
        gene_mapping: Optional[dict[str, str]] = None,
        nrows: Optional[int] = None,
    ) -> bool:
        ...


class GeneModels(
    ResourceConfigValidationMixin,
):
    """Provides class for gene models."""

    def __init__(self, resource: GenomicResource):
        if resource.get_type() != "gene_models":
            raise ValueError(
                f"wrong type of resource passed: {resource.get_type()}")
        self.resource = resource
        self.config = self.validate_and_normalize_schema(
            resource.get_config(), resource,
        )

        self.gene_models: dict[str, list[TranscriptModel]] = defaultdict(list)
        self.utr_models: dict[
                str, dict[tuple[int, int], list[TranscriptModel]]] = \
            defaultdict(lambda: defaultdict(list))
        self.transcript_models: dict[str, Any] = {}
        self.alternative_names: dict[str, Any] = {}

        self._reset()

    @property
    def resource_id(self) -> str:
        return self.resource.resource_id

    def _reset(self) -> None:
        self.alternative_names = {}

        self.utr_models = defaultdict(lambda: defaultdict(list))
        self.transcript_models = {}
        self.gene_models = defaultdict(list)

    def _add_transcript_model(self, transcript_model: TranscriptModel) -> None:

        assert transcript_model.tr_id not in self.transcript_models

        self.transcript_models[transcript_model.tr_id] = transcript_model
        self.gene_models[transcript_model.gene].append(transcript_model)

        self.utr_models[transcript_model.chrom][transcript_model.tx]\
            .append(transcript_model)

    def update_indexes(self) -> None:
        self.gene_models = defaultdict(list)
        self.utr_models = defaultdict(lambda: defaultdict(list))
        for transcript in self.transcript_models.values():
            self.gene_models[transcript.gene].append(transcript)
            self.utr_models[transcript.chrom][transcript.tx].append(transcript)

    def gene_names(self) -> list[str]:
        if self.gene_models is None:
            logger.warning(
                "gene models %s are empty", self.resource.resource_id)
            return []

        return list(self.gene_models.keys())

    def gene_models_by_gene_name(
        self, name: str,
    ) -> Optional[list[TranscriptModel]]:
        return self.gene_models.get(name, None)

    def gene_models_by_location(
        self, chrom: str, pos1: int,
        pos2: Optional[int] = None,
    ) -> list[TranscriptModel]:
        """Retrieve TranscriptModel objects based on genomic position(s).

        Args:
            chrom (str): The chromosome name.
            pos1 (int): The starting genomic position.
            pos2 (Optional[int]): The ending genomic position. If not provided,
                only models that contain pos1 will be returned.

        Returns:
            list[TranscriptModel]: A list of TranscriptModel objects that
                match the given location criteria.
        """
        result = []

        if pos2 is None:
            key: tuple[int, int]
            for key in self.utr_models[chrom]:
                if key[0] <= pos1 <= key[1]:
                    result.extend(self.utr_models[chrom][key])

        else:
            if pos2 < pos1:
                pos1, pos2 = pos2, pos1

            for key in self.utr_models[chrom]:
                if pos1 <= key[0] <= pos2 or key[0] <= pos1 <= key[1]:
                    result.extend(self.utr_models[chrom][key])

        return result

    def relabel_chromosomes(
        self, relabel: Optional[dict[str, str]] = None,
        map_file: Optional[str] = None,
    ) -> None:
        """Relabel chromosomes in gene model."""
        assert relabel or map_file
        if not relabel:
            assert map_file is not None
            with open(map_file) as infile:
                relabel = cast(
                    dict[str, str],
                    {
                        line.strip("\n\r").split()[:2] for line in infile
                    },
                )

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

        for transcript_model in self.transcript_models.values():
            transcript_model.chrom = relabel[transcript_model.chrom]

    def _save_gene_models(self, outfile: IO) -> None:
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
                ],
            ),
        )
        outfile.write("\n")

        for transcript_model in self.transcript_models.values():
            exon_starts = ",".join([
                str(e.start) for e in transcript_model.exons])
            exon_ends = ",".join([
                str(e.stop) for e in transcript_model.exons])
            exon_frames = ",".join([
                str(e.frame) for e in transcript_model.exons])

            add_atts = ";".join(
                [
                    k + ":" + str(v).replace(":", "_")
                    for k, v in list(transcript_model.attributes.items())
                ],
            )

            columns = [
                transcript_model.chrom,
                transcript_model.tr_id,
                transcript_model.tr_name,
                transcript_model.gene,
                transcript_model.strand,
                transcript_model.tx[0],
                transcript_model.tx[1],
                transcript_model.cds[0],
                transcript_model.cds[1],
                exon_starts,
                exon_ends,
                exon_frames,
                add_atts,
            ]
            outfile.write("\t".join([str(x) if x else "" for x in columns]))
            outfile.write("\n")

    def to_gtf(self) -> str:
        """Output a GTF format string representation."""
        if not self.gene_models:
            return ""

        buffer = StringIO()
        tmpl = \
            "gene\t{0}\t{1}\t.\t{2}\t.\t{3}"

        buffer.write(f"""
##description: auto-generated GTF-format dump for gene models "{self.resource.resource_id}"
##provider: SEQPIPE
##format: gtf
##date: {datetime.today().strftime('%Y-%m-%d')}
""")  # noqa: E501

        for gene_name, transcripts in self.gene_models.items():
            t = transcripts[0]

            chrom = t.chrom
            start = min(t.tx[0] for t in transcripts)
            stop = max(t.tx[1] for t in transcripts)
            strand = t.strand
            gene_id = t.attributes.get("gene_id", gene_name)
            version = t.attributes.get("gene_version", ".")
            src = t.attributes.get("gene_source", ".")
            biotype = t.attributes.get("gene_biotype", ".")
            attrs = [f'gene_id "{gene_id}"',
                     f'gene_version "{version}"',
                     f'gene_name "{gene_name}"',
                     f'gene_source "{src}"',
                     f'gene_biotype "{biotype}"']

            buffer.write(f"{chrom}\t{src}\t")
            buffer.write(tmpl.format(start, stop, strand, ";".join(attrs)))
            buffer.write(";\n")
            for transcript in transcripts:
                buffer.write(transcript.to_gtf())
                buffer.write("\n")

        res = buffer.getvalue()
        buffer.close()
        return res

    def save(self, output_filename: str, *, gzipped: bool = True) -> None:
        """Save gene models in a file in default file format."""
        if gzipped:
            if not output_filename.endswith(".gz"):
                output_filename = f"{output_filename}.gz"
            with gzip.open(output_filename, "wt") as outfile:
                self._save_gene_models(outfile)
        else:

            with open(output_filename, "wt") as outfile:
                self._save_gene_models(outfile)

    def _parse_default_gene_models_format(
        self, infile: IO,
        gene_mapping: Optional[dict[str, str]] = None,
        nrows: Optional[int] = None,
    ) -> bool:
        # pylint: disable=too-many-locals
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

        if gene_mapping:
            self.alternative_names = copy.deepcopy(gene_mapping)

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
                attributes = {
                    a[0]: a[1] for a in astep
                }
            gene = line["gene"]
            gene = self.alternative_names.get(gene, gene)
            transcript_model = TranscriptModel(
                gene=gene,
                tr_id=line["trID"],
                tr_name=line["trOrigId"],
                chrom=line["chr"],
                strand=line["strand"],
                tx=(line["tsBeg"], line["txEnd"]),
                cds=(line["cdsStart"], line["cdsEnd"]),
                exons=exons,
                attributes=attributes,
            )
            self.transcript_models[transcript_model.tr_id] = transcript_model

        self.update_indexes()
        if nrows is not None:
            return True

        return True

    def _parse_ref_flat_gene_models_format(
        self, infile: IO,
        gene_mapping: Optional[dict[str, str]] = None,
        nrows: Optional[int] = None,
    ) -> bool:
        # pylint: disable=too-many-locals
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

        transcript_ids_counter: dict[str, int] = defaultdict(int)
        if gene_mapping:
            self.alternative_names = copy.deepcopy(gene_mapping)

        for rec in records:
            gene = rec["#geneName"]
            gene = self.alternative_names.get(gene, gene)
            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (  # pylint: disable=invalid-name
                int(rec["txStart"]) + 1, int(rec["txEnd"]))
            cds = (int(rec["cdsStart"]) + 1, int(rec["cdsEnd"]))

            exon_starts = list(map(
                int, str(rec["exonStarts"]).strip(",").split(",")))
            exon_ends = list(map(
                int, str(rec["exonEnds"]).strip(",").split(",")))
            assert len(exon_starts) == len(exon_ends)

            exons = [
                Exon(start + 1, end)
                for start, end in zip(exon_starts, exon_ends)
            ]

            transcript_ids_counter[tr_name] += 1
            tr_id = f"{tr_name}_{transcript_ids_counter[tr_name]}"

            transcript_model = TranscriptModel(
                gene=gene,
                tr_id=tr_id,
                tr_name=tr_name,
                chrom=chrom,
                strand=strand,
                tx=tx,
                cds=cds,
                exons=exons,
            )
            transcript_model.update_frames()
            self._add_transcript_model(transcript_model)

        return True

    def _parse_ref_seq_gene_models_format(
        self, infile: IO,
        gene_mapping: Optional[dict[str, str]] = None,
        nrows: Optional[int] = None,
    ) -> bool:
        # pylint: disable=too-many-locals
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

        transcript_ids_counter: dict[str, int] = defaultdict(int)
        if gene_mapping:
            self.alternative_names = copy.deepcopy(gene_mapping)

        for rec in records:
            gene = rec["name2"]
            gene = self.alternative_names.get(gene, gene)

            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (  # pylint: disable=invalid-name
                int(rec["txStart"]) + 1, int(rec["txEnd"]))
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
            transcript_model = TranscriptModel(
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
            transcript_model.update_frames()
            self._add_transcript_model(transcript_model)

        return True

    @classmethod
    def _probe_header(
        cls, infile: IO, expected_columns: list[str],
        comment: Optional[str] = None,
    ) -> bool:
        infile.seek(0)
        df = pd.read_csv(
            infile, sep="\t", nrows=1, header=None, comment=comment)
        return list(df.iloc[0, :]) == expected_columns

    @classmethod
    def _probe_columns(
        cls, infile: IO, expected_columns: list[str],
        comment: Optional[str] = None) -> bool:
        infile.seek(0)
        df = pd.read_csv(
            infile, sep="\t", nrows=1, header=None, comment=comment)
        return cast(list[int], list(df.columns)) == \
            list(range(len(expected_columns)))

    @classmethod
    def _parse_raw(
        cls, infile: IO, expected_columns: list[str],
        nrows: Optional[int] = None, comment: Optional[str] = None,
    ) -> Optional[pd.DataFrame]:
        if cls._probe_header(infile, expected_columns, comment=comment):
            infile.seek(0)
            df = pd.read_csv(infile, sep="\t", nrows=nrows, comment=comment)
            assert list(df.columns) == expected_columns
            return df

        if cls._probe_columns(infile, expected_columns, comment=comment):
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
        return None

    def _parse_ccds_gene_models_format(
        self, infile: IO,
        gene_mapping: Optional[dict[str, str]] = None,
        nrows: Optional[int] = None,
    ) -> bool:
        # pylint: disable=too-many-locals
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

        transcript_ids_counter: dict[str, int] = defaultdict(int)
        if gene_mapping:
            self.alternative_names = copy.deepcopy(gene_mapping)

        for rec in records:
            gene = rec["name"]
            gene = self.alternative_names.get(gene, gene)

            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (  # pylint: disable=invalid-name
                int(rec["txStart"]) + 1, int(rec["txEnd"]))
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
            transcript_model = TranscriptModel(
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
            transcript_model.update_frames()
            self._add_transcript_model(transcript_model)

        return True

    def _parse_known_gene_models_format(
        self, infile: IO,
        gene_mapping: Optional[dict[str, str]] = None,
        nrows: Optional[int] = None,
    ) -> bool:
        # pylint: disable=too-many-locals
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

        transcript_ids_counter: dict[str, int] = defaultdict(int)

        if gene_mapping:
            self.alternative_names = copy.deepcopy(gene_mapping)

        for rec in records:
            gene = rec["name"]
            gene = self.alternative_names.get(gene, gene)

            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (  # pylint: disable=invalid-name
                int(rec["txStart"]) + 1, int(rec["txEnd"]))
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
            transcript_model = TranscriptModel(
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
            transcript_model.update_frames()
            self._add_transcript_model(transcript_model)

        return True

    def _parse_ucscgenepred_models_format(
        self, infile: IO,
        gene_mapping: Optional[dict[str, str]] = None,
        nrows: Optional[int] = None,
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
        # pylint: disable=too-many-locals
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

        transcript_ids_counter: dict[str, int] = defaultdict(int)
        if gene_mapping:
            self.alternative_names = copy.deepcopy(gene_mapping)

        for rec in records:
            gene = rec.get("name2")
            if not gene:
                gene = rec["name"]
            gene = self.alternative_names.get(gene, gene)

            tr_name = rec["name"]
            chrom = rec["chrom"]
            strand = rec["strand"]
            tx = (  # pylint: disable=invalid-name
                int(rec["txStart"]) + 1, int(rec["txEnd"]))
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
            transcript_model = TranscriptModel(
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
            transcript_model.update_frames()
            self._add_transcript_model(transcript_model)

        return True

    @staticmethod
    def _parse_gtf_attributes(data: str) -> dict[str, str]:
        attributes = list(
            filter(lambda x: x, [a.strip() for a in data.split(";")]),
        )
        result = {}
        for attr in attributes:
            key, value = attr.split(" ", maxsplit=1)
            result[key.strip()] = value.strip('"').strip()
        return result

    def _parse_gtf_gene_models_format(
        self, infile: IO,
        gene_mapping: Optional[dict[str, str]] = None,
        nrows: Optional[int] = None,
    ) -> bool:
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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
            infile, expected_columns, nrows=nrows, comment="#")
        if df is None:
            expected_columns.append("comment")
            infile.seek(0)
            df = self._parse_raw(
                infile, expected_columns, nrows=nrows, comment="#")
            if df is None:
                return False

        if gene_mapping:
            self.alternative_names = copy.deepcopy(gene_mapping)

        records = df.to_dict(orient="records")
        for rec in records:
            feature = rec["feature"]
            if feature == "gene":
                continue
            attributes = self._parse_gtf_attributes(rec["attributes"])
            tr_id = attributes["transcript_id"]
            if feature in {"transcript", "Selenocysteine"}:
                if feature == "Selenocysteine" and \
                        tr_id in self.transcript_models:
                    continue
                if tr_id in self.transcript_models:
                    raise ValueError(
                        f"{tr_id} of {feature} already in transcript models",
                    )
                gene = attributes["gene_name"]
                gene = self.alternative_names.get(gene, gene)

                transcript_model = TranscriptModel(
                    gene=gene,
                    tr_id=tr_id,
                    tr_name=tr_id,
                    chrom=rec["seqname"],
                    strand=rec["strand"],
                    tx=(rec["start"], rec["end"]),
                    cds=(rec["end"], rec["start"]),
                    attributes=attributes,
                )
                self._add_transcript_model(transcript_model)
                continue
            if feature == "exon":
                if tr_id not in self.transcript_models:
                    raise ValueError(
                        f"exon or CDS transcript {tr_id} not found "
                        f"in transctipt models",
                    )
                transcript_model = self.transcript_models[tr_id]
                if feature == "exon":
                    exon = Exon(
                        rec["start"], rec["end"], frame=-1,
                    )
                    transcript_model.exons.append(exon)
                    continue
            if feature in {"UTR", "5UTR", "3UTR", "CDS"}:
                continue
            if feature in {"start_codon", "stop_codon"}:
                transcript_model = self.transcript_models[tr_id]
                cds = transcript_model.cds
                transcript_model.cds = \
                    (min(cds[0], rec["start"]), max(cds[1], rec["end"]))
                continue

            raise ValueError(
                f"unknown feature {feature} found in gtf gene models")

        for transcript_model in self.transcript_models.values():
            transcript_model.exons = sorted(
                transcript_model.exons, key=lambda x: x.start)
            transcript_model.update_frames()

        return True

    @classmethod
    def _load_gene_mapping(cls, infile: IO) -> dict[str, str]:
        """Load alternative names for genes.

        Assume that its first line has two column names
        """
        df = pd.read_csv(infile, sep="\t")
        assert len(df.columns) == 2

        df = df.rename(columns={df.columns[0]: "tr_id", df.columns[1]: "gene"})

        records = df.to_dict(orient="records")

        alt_names = {}
        for rec in records:
            rec = cast(dict, rec)
            alt_names[rec["tr_id"]] = rec["gene"]

        return alt_names

    SUPPORTED_GENE_MODELS_FILE_FORMATS: ClassVar[set[str]] = {
        "default",
        "refflat",
        "refseq",
        "ccds",
        "knowngene",
        "gtf",
        "ucscgenepred",
    }

    def _get_parser(
        self, fileformat: str,
    ) -> Optional[GeneModelsParser]:
        # pylint: disable=too-many-return-statements
        if fileformat == "default":
            return self._parse_default_gene_models_format
        if fileformat == "refflat":
            return self._parse_ref_flat_gene_models_format
        if fileformat == "refseq":
            return self._parse_ref_seq_gene_models_format
        if fileformat == "ccds":
            return self._parse_ccds_gene_models_format
        if fileformat == "knowngene":
            return self._parse_known_gene_models_format
        if fileformat == "gtf":
            return self._parse_gtf_gene_models_format
        if fileformat == "ucscgenepred":
            return self._parse_ucscgenepred_models_format
        return None

    def _infer_gene_model_parser(
        self, infile: IO,
        file_format: Optional[str] = None) -> Optional[str]:

        if file_format is not None:
            parser = self._get_parser(file_format)
            if parser is not None:
                return file_format

        logger.info("going to infer gene models file format...")
        inferred_formats = []
        for inferred_format in self.SUPPORTED_GENE_MODELS_FILE_FORMATS:
            parser = self._get_parser(inferred_format)
            if parser is None:
                continue
            try:
                logger.debug("trying file format: %s...", inferred_format)
                self._reset()
                infile.seek(0)
                res = parser(infile, nrows=50)
                if res:
                    inferred_formats.append(inferred_format)
                    logger.debug(
                        "gene models format %s matches input", inferred_format)
            except Exception as ex:  # noqa: BLE001 pylint: disable=broad-except
                logger.debug(
                    "file format %s does not match; %s",
                    inferred_format, ex, exc_info=True)

        logger.info("inferred file formats: %s", inferred_formats)
        if len(inferred_formats) == 1:
            return inferred_formats[0]

        logger.error(
            "can't find gene model parser; "
            "inferred file formats are %s", inferred_formats)
        return None

    def is_loaded(self) -> bool:
        return len(self.transcript_models) > 0

    def probe_file_format(self) -> Optional[str]:
        """Probe gene models file format."""
        filename = self.resource.get_config()["filename"]
        logger.debug("checing gene models %s file format", filename)
        compression = False
        if filename.endswith(".gz"):
            compression = True
        with self.resource.open_raw_file(
                filename, mode="rt", compression=compression) as infile:

            return self._infer_gene_model_parser(infile)

    def load(self) -> GeneModels:
        """Load gene models."""
        if self.is_loaded():
            logger.info(
                "loading already loaded gene models: %s",
                self.resource.resource_id)
            return self

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
                raise ValueError

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
                    gene_mapping = self._load_gene_mapping(gene_mapping_file)

            infile.seek(0)
            self._reset()

            if not parser(infile, gene_mapping=gene_mapping):
                raise ValueError(
                    f"Failed to parse gene models file {filename} "
                    f"with format {fileformat}")
        return self

    @staticmethod
    def get_schema() -> dict[str, Any]:
        return {
            **get_base_resource_schema(),
            "filename": {"type": "string"},
            "format": {"type": "string"},
            "gene_mapping": {"type": "string"},
        }


def join_gene_models(*gene_models: GeneModels) -> GeneModels:
    """Join muliple gene models into a single gene models object."""
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
    file_name: str,
    file_format: Optional[str] = None,
    gene_mapping_file_name: Optional[str] = None,
) -> GeneModels:
    """Load gene models from local filesystem."""
    config = {
        "type": "gene_models",
        "filename": file_name,
    }
    if file_format:
        config["format"] = file_format
    if gene_mapping_file_name:
        config["gene_mapping"] = gene_mapping_file_name

    res = build_local_resource(".", config)
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

    return GeneModels(resource)


def create_regions_from_genes(
    gene_models: GeneModels,
    genes: list[str],
    regions: Optional[list[Region]],
    gene_regions_heuristic_cutoff: int = 20,
    gene_regions_heuristic_extend: int = 20000,
) -> Optional[list[Region]]:
    """Produce a list of regions from given gene symbols.

    If given a list of regions, will merge the newly-created regions
    from the genes with the provided ones.
    """
    assert genes is not None
    assert gene_models is not None

    if len(genes) == 0 or len(genes) > gene_regions_heuristic_cutoff:
        return regions

    gene_regions = []
    for gene_name in genes:
        gene_model = gene_models.gene_models_by_gene_name(gene_name)
        if gene_model is None:
            logger.warning("gene model for %s not found", gene_name)
            continue
        for gm in gene_model:
            gene_regions.append(  # noqa: PERF401
                Region(
                    gm.chrom,
                    max(1, gm.tx[0] - 1 - gene_regions_heuristic_extend),
                    gm.tx[1] + 1 + gene_regions_heuristic_extend,
                ),
            )

    gene_regions = collapse(gene_regions)
    if not regions:
        regions = gene_regions
    else:
        result = []
        for gene_region in gene_regions:
            for region in regions:
                intersection = gene_region.intersection(region)
                if intersection:
                    result.append(intersection)
        result = collapse(result)
        logger.info("original regions: %s; result: %s", regions, result)
        regions = result

    return regions
