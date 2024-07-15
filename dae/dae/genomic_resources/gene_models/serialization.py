import gzip
import logging
import operator
from datetime import datetime
from typing import IO

from deprecation import deprecated

from dae.utils.regions import BedRegion, difference, total_length

from .gene_models import (
    Exon,
    GeneModels,
    TranscriptModel,
)

logger = logging.getLogger(__name__)


GTF_FEATURE_ORDER = ("gene", "transcript", "exon", "CDS",
                     "start_codon", "stop_codon", "UTR")
GTFRecordIndex = tuple[str, int, int, int]
GTFRecord = tuple[GTFRecordIndex, str]


def gene_models_to_gtf(gene_models: GeneModels) -> str:
    """Output a GTF format string representation."""
    if not gene_models.gene_models:
        logger.warning("Serializing empty (probably not loaded) gene models!")
        return ""

    record_buffer: list[GTFRecord] = []

    for gene_name, transcripts in gene_models.gene_models.items():
        t = transcripts[0]
        chrom = t.chrom
        start = min(t.tx[0] for t in transcripts)
        stop = max(t.tx[1] for t in transcripts)
        strand = t.strand
        gene_id = t.attributes.get("gene_id", gene_name)
        version = t.attributes.get("gene_version", ".")
        src = t.attributes.get("gene_source", ".")
        biotype = t.attributes.get("gene_biotype", ".")
        attrs = ";".join([
            f'gene_id "{gene_id}"',
            f'gene_version "{version}"',
            f'gene_name "{gene_name}"',
            f'gene_source "{src}"',
            f'gene_biotype "{biotype}"',
        ])

        gene_rec = \
            f"{chrom}\t{src}\tgene\t{start}\t{stop}\t.\t{strand}\t.\t{attrs};"
        record_buffer.append(
            ((chrom, start, -stop, GTF_FEATURE_ORDER.index("gene")), gene_rec))
        for transcript in transcripts:
            record_buffer.extend(transcript_to_gtf(transcript))

    record_buffer.sort(key=operator.itemgetter(0))

    joined_records = "\n".join(rec[1] for rec in record_buffer)
    return \
f"""##description: GTF format dump for gene models "{gene_models.resource.resource_id or '?'}"
##provider: GPF
##format: gtf
##date: {datetime.today().strftime('%Y-%m-%d')}
{joined_records}
"""  # noqa: E501


def build_gtf_record(
    transcript: TranscriptModel,
    feature: str,
    start: int, stop: int,
    attrs: str,
) -> GTFRecord:
    """Build an indexed GTF format record for a feature."""
    src = transcript.attributes.get("gene_source", ".")
    phase = "."
    exon_number = -1
    if feature in ("exon", "CDS", "start_codon", "stop_codon"):
        exon_number = transcript.get_exon_number_for(start, stop)

    if feature in ("CDS", "start_codon", "stop_codon"):
        frame = calc_frame_for_gtf_cds_feature(
            transcript, BedRegion(transcript.chrom, start, stop))
        phase = str((3 - frame) % 3)

    line = (f"{transcript.chrom}\t{src}\t{feature}\t{start}"
            f"\t{stop}\t.\t{transcript.strand}\t{phase}\t{attrs};")

    if feature in ("exon", "CDS", "start_codon", "stop_codon"):
        line = f'{line}exon_number "{exon_number}";'
    # add stop as negative to sort it in descending order
    index = \
        (transcript.chrom, start, -stop, GTF_FEATURE_ORDER.index(feature))
    return (index, line)


@deprecated("This function was split into multiple specialized functions.")
def collect_cds_regions(
    transcript: TranscriptModel,
) -> tuple[list[BedRegion], list[BedRegion], list[BedRegion]]:
    """
    Returns a tuple of start codon regions, normal coding regions
    and stop codon regions for a given transcript.
    """
    if not transcript.is_coding():
        return ([], [], [])
    reverse = transcript.strand == "-"
    start_codons: list[BedRegion] = []
    cds_regions: list[BedRegion] = transcript.cds_regions()
    stop_codons: list[BedRegion] = []

    start_bases_remaining, stop_bases_remaining = 3, 3

    while start_bases_remaining > 0:
        cds = cds_regions.pop(0 if not reverse else -1)
        cds_len = cds.stop - cds.start + 1
        bases_to_write = min(start_bases_remaining, cds_len)

        codon_start = cds.start if not reverse \
                      else cds.stop - (bases_to_write - 1)
        codon_stop = codon_start + (bases_to_write - 1) if not reverse \
                     else cds.stop
        start_codons.append(BedRegion(cds.chrom, codon_start, codon_stop))

        if cds_len - bases_to_write > 0:
            cds_regions.insert(0 if not reverse else -1, cds)

        start_bases_remaining -= bases_to_write

    while stop_bases_remaining > 0:
        cds = cds_regions.pop(-1 if not reverse else 0)
        cds_len = cds.stop - cds.start + 1
        bases_to_write = min(stop_bases_remaining, cds_len)

        codon_start = cds.stop - (bases_to_write - 1) if not reverse \
                      else cds.start
        codon_stop = cds.stop if not reverse \
                     else codon_start + (bases_to_write - 1)
        stop_codons.append(BedRegion(cds.chrom, codon_start, codon_stop))

        if cds_len - bases_to_write > 0:
            remainder = BedRegion(
                cds.chrom,
                cds.start if not reverse else codon_stop + 1,
                codon_start - 1 if not reverse else cds.stop,
            )
            cds_regions.insert(-1 if not reverse else 0, remainder)

        stop_bases_remaining -= bases_to_write

    return start_codons, cds_regions, stop_codons


def collect_gtf_start_codon_regions(
    strand: str,
    cds_regions: list[BedRegion],
) -> list[BedRegion]:
    """Returns list of all regions that represent the start codon."""
    if strand == "+":
        region = cds_regions[0]
        if len(region) >= 3:
            return [
                BedRegion(
                    region.chrom,
                    region.start,
                    region.start + 2,
                ),
            ]
        result = [region]
        for region in cds_regions[1:]:
            total = total_length(result)
            if total + len(region) >= 3:
                result.append(BedRegion(
                    region.chrom,
                    region.start,
                    region.start + (2 - total),
                ))
                return result
            result.append(region)

    elif strand == "-":
        region = cds_regions[-1]
        if len(region) >= 3:
            return [
                BedRegion(
                    region.chrom,
                    region.stop - 2,
                    region.stop,
                ),
            ]
        result = [region]
        for region in reversed(cds_regions[:-1]):
            total = total_length(result)
            if total + len(region) >= 3:
                result.append(BedRegion(
                    region.chrom,
                    region.stop - (2 - total),
                    region.stop,
                ))
                return list(reversed(result))
            result.append(region)
    else:
        raise ValueError("Invalid strand")
    return []


def collect_gtf_stop_codon_regions(
    strand: str,
    cds_regions: list[BedRegion],
) -> list[BedRegion]:
    """Returns list of all regions that represent the stop codon."""
    if strand == "+":
        region = cds_regions[-1]
        if len(region) >= 3:
            return [
                BedRegion(
                    region.chrom,
                    region.stop - 2,
                    region.stop,
                ),
            ]
        result = [region]
        for region in reversed(cds_regions[:-1]):
            total = total_length(result)
            if total + len(region) >= 3:
                result.append(BedRegion(
                    region.chrom,
                    region.stop - (2 - total),
                    region.stop,
                ))
                return list(reversed(result))
            result.append(region)

    elif strand == "-":
        region = cds_regions[0]
        if len(region) >= 3:
            return [
                BedRegion(
                    region.chrom,
                    region.start,
                    region.start + 2,
                ),
            ]
        result = [region]
        for region in cds_regions[1:]:
            total = total_length(result)
            if total + len(region) >= 3:
                result.append(BedRegion(
                    region.chrom,
                    region.start,
                    region.start + (2 - total),
                ))
                return result
            result.append(region)
    else:
        raise ValueError("Invalid strand")
    return []


def collect_gtf_cds_regions(
    strand: str,
    cds_regions: list[BedRegion],
) -> list[BedRegion]:
    """Returns list of all regions that represent the CDS."""
    stop_codon_regions = collect_gtf_stop_codon_regions(strand, cds_regions)

    return difference(cds_regions, stop_codon_regions)  # type: ignore


def find_exon_cds_region_for_gtf_cds_feature(
    transcript: TranscriptModel,
    region: BedRegion,
) -> tuple[Exon, BedRegion]:
    """Find exon and CDS region that contains the given feature."""
    for exon in transcript.exons:
        if exon.contains((region.start, region.stop)):
            for cds_region in transcript.cds_regions():
                if exon.contains((cds_region.start, cds_region.stop)):
                    return exon, cds_region
    raise ValueError(f"exon for region {region} not found")


def calc_frame_for_gtf_cds_feature(
    transcript: TranscriptModel,
    region: BedRegion,
) -> int:
    """Calculate frame for the given feature."""
    exon, cds_region = find_exon_cds_region_for_gtf_cds_feature(
        transcript, region)
    if exon.frame is None:
        raise ValueError(f"frame not found for exon {exon}")
    if transcript.strand == "+":
        return (exon.frame + (abs(cds_region.start - region.start) % 3)) % 3
    return (exon.frame + (abs(cds_region.stop - region.stop) % 3)) % 3


def transcript_to_gtf(transcript: TranscriptModel) -> list[GTFRecord]:
    """Output an indexed list of GTF-formatted features of a transcript."""
    record_buffer: list[GTFRecord] = []

    attributes = dict(transcript.attributes)
    if "gene_name" not in attributes:
        attributes["gene_name"] = transcript.gene
    if "gene_id" not in attributes:
        attributes["gene_id"] = transcript.gene
    str_attrs = ";".join(f'{k} "{v}"' for k, v in attributes.items())

    def write_record(feature: str, start: int, stop: int) -> None:
        record_buffer.append(
            build_gtf_record(transcript, feature, start, stop, str_attrs))

    write_record("transcript", transcript.tx[0], transcript.tx[1])

    for exon in transcript.exons:
        write_record("exon", exon.start, exon.stop)

    if transcript.is_coding():
        cds_regions = transcript.cds_regions()
        for codon in collect_gtf_start_codon_regions(
                transcript.strand, cds_regions):
            write_record("start_codon", codon.start, codon.stop)

        for cds in collect_gtf_cds_regions(
                transcript.strand, cds_regions):
            write_record("CDS", cds.start, cds.stop)

        for codon in collect_gtf_stop_codon_regions(
                transcript.strand, cds_regions):
            write_record("stop_codon", codon.start, codon.stop)

        for utr in transcript.utr3_regions() + transcript.utr5_regions():
            write_record("UTR", utr.start, utr.stop)

    return record_buffer


def _save_as_default_gene_models(
    gene_models: GeneModels,
    outfile: IO,
) -> None:
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

    for transcript_model in gene_models.transcript_models.values():
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


def save_as_default_gene_models(
    gene_models: GeneModels,
    output_filename: str, *,
    gzipped: bool = True,
) -> None:
    """Save gene models in a file in default file format."""
    if gzipped:
        if not output_filename.endswith(".gz"):
            output_filename = f"{output_filename}.gz"
        with gzip.open(output_filename, "wt") as outfile:
            _save_as_default_gene_models(gene_models, outfile)
    else:

        with open(output_filename, "wt") as outfile:
            _save_as_default_gene_models(gene_models, outfile)
