from __future__ import annotations

import copy
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import IO, cast

import pandas as pd

from .gene_models import (
    Exon,
    GeneModels,
    TranscriptModel,
)

logger = logging.getLogger(__name__)


GeneModelsParser = Callable[
    [GeneModels, IO, dict[str, str] | None, int | None],
    bool,
]


def parse_default_gene_models_format(
    gene_models: GeneModels,
    infile: IO,
    gene_mapping: dict[str, str] | None = None,
    nrows: int | None = None,
) -> bool:
    """Parse default gene models file format."""
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
        gene_models.alternative_names = copy.deepcopy(gene_mapping)

    records = df.to_dict(orient="records")
    for line in records:
        line = cast(dict, line)
        exon_starts = list(map(int, line["exonStarts"].split(",")))
        exon_ends = list(map(int, line["exonEnds"].split(",")))
        exon_frames = list(map(int, line["exonFrames"].split(",")))
        assert len(exon_starts) == len(exon_ends) == len(exon_frames)

        exons = []
        for start, end, frame in zip(exon_starts, exon_ends, exon_frames,
                                        strict=True):
            exons.append(Exon(start=start, stop=end, frame=frame))
        attributes: dict = {}
        atts = line.get("atts")
        if atts and isinstance(atts, str):
            astep = [a.split(":") for a in atts.split(";")]
            attributes = {
                a[0]: a[1] for a in astep
            }
        gene = line["gene"]
        gene = gene_models.alternative_names.get(gene, gene)
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
        gene_models.transcript_models[transcript_model.tr_id] = transcript_model

    gene_models.update_indexes()
    if nrows is not None:
        return True

    return True


def parse_ref_flat_gene_models_format(
    gene_models: GeneModels,
    infile: IO,
    gene_mapping: dict[str, str] | None = None,
    nrows: int | None = None,
) -> bool:
    """Parse refFlat gene models file format."""
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
    df = parse_raw(infile, expected_columns, nrows=nrows)
    if df is None:
        return False

    records = df.to_dict(orient="records")

    transcript_ids_counter: dict[str, int] = defaultdict(int)
    if gene_mapping:
        gene_models.alternative_names = copy.deepcopy(gene_mapping)

    for rec in records:
        gene = rec["#geneName"]
        gene = gene_models.alternative_names.get(gene, gene)
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
            for start, end in zip(exon_starts, exon_ends, strict=True)
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
        gene_models.add_transcript_model(transcript_model)

    return True


def parse_ref_seq_gene_models_format(
    gene_models: GeneModels,
    infile: IO,
    gene_mapping: dict[str, str] | None = None,
    nrows: int | None = None,
) -> bool:
    """Parse refSeq gene models file format."""
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
    df = parse_raw(infile, expected_columns, nrows=nrows)
    if df is None:
        return False

    records = df.to_dict(orient="records")

    transcript_ids_counter: dict[str, int] = defaultdict(int)
    if gene_mapping:
        gene_models.alternative_names = copy.deepcopy(gene_mapping)

    for rec in records:
        gene = rec["name2"]
        gene = gene_models.alternative_names.get(gene, gene)

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
            for start, end in zip(exon_starts, exon_ends, strict=True)
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
        gene_models.add_transcript_model(transcript_model)

    return True


def probe_header(
    infile: IO, expected_columns: list[str],
    comment: str | None = None,
) -> bool:
    """Probe gene models file header based on expected columns."""
    infile.seek(0)
    df = pd.read_csv(
        infile, sep="\t", nrows=1, header=None, comment=comment)
    return list(df.iloc[0, :]) == expected_columns


def probe_columns(
    infile: IO, expected_columns: list[str],
    comment: str | None = None,
) -> bool:
    """Probe gene models file based on expected columns."""
    infile.seek(0)
    df = pd.read_csv(
        infile, sep="\t", nrows=1, header=None, comment=comment)
    return cast(list[int], list(df.columns)) == \
        list(range(len(expected_columns)))


def parse_raw(
    infile: IO, expected_columns: list[str],
    nrows: int | None = None, comment: str | None = None,
) -> pd.DataFrame | None:
    """Parse raw gene models data based on expected columns."""
    if probe_header(infile, expected_columns, comment=comment):
        infile.seek(0)
        df = pd.read_csv(infile, sep="\t", nrows=nrows, comment=comment)
        assert list(df.columns) == expected_columns
        return df

    if probe_columns(infile, expected_columns, comment=comment):
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


def parse_ccds_gene_models_format(
    gene_models: GeneModels,
    infile: IO,
    gene_mapping: dict[str, str] | None = None,
    nrows: int | None = None,
) -> bool:
    """Parse CCDS gene models file format."""
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
    df = parse_raw(infile, expected_columns, nrows=nrows)
    if df is None:
        return False

    records = df.to_dict(orient="records")

    transcript_ids_counter: dict[str, int] = defaultdict(int)
    if gene_mapping:
        gene_models.alternative_names = copy.deepcopy(gene_mapping)

    for rec in records:
        gene = rec["name"]
        gene = gene_models.alternative_names.get(gene, gene)

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
            for start, end in zip(exon_starts, exon_ends, strict=True)
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
        gene_models.add_transcript_model(transcript_model)

    return True


def parse_known_gene_models_format(
    gene_models: GeneModels,
    infile: IO,
    gene_mapping: dict[str, str] | None = None,
    nrows: int | None = None,
) -> bool:
    """Parse known gene models file format."""
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
    df = parse_raw(infile, expected_columns, nrows=nrows)
    if df is None:
        return False

    records = df.to_dict(orient="records")

    transcript_ids_counter: dict[str, int] = defaultdict(int)

    if gene_mapping:
        gene_models.alternative_names = copy.deepcopy(gene_mapping)

    for rec in records:
        gene = rec["name"]
        gene = gene_models.alternative_names.get(gene, gene)

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
            for start, end in zip(exon_starts, exon_ends, strict=True)
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
        gene_models.add_transcript_model(transcript_model)

    return True


def parse_ucscgenepred_models_format(
    gene_models: GeneModels,
    infile: IO,
    gene_mapping: dict[str, str] | None = None,
    nrows: int | None = None,
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
    df = parse_raw(infile, expected_columns[:10], nrows=nrows)
    if df is None:
        infile.seek(0)
        df = parse_raw(infile, expected_columns, nrows=nrows)
        if df is None:
            return False

    records = df.to_dict(orient="records")

    transcript_ids_counter: dict[str, int] = defaultdict(int)
    if gene_mapping:
        gene_models.alternative_names = copy.deepcopy(gene_mapping)

    for rec in records:
        gene = rec.get("name2")
        if not gene:
            gene = rec["name"]
        gene = gene_models.alternative_names.get(gene, gene)

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
            for start, end in zip(exon_starts, exon_ends, strict=True)
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
        gene_models.add_transcript_model(transcript_model)

    return True


def _parse_gtf_attributes(data: str) -> dict[str, str]:
    attributes = list(
        filter(lambda x: x, [a.strip() for a in data.split(";")]),
    )
    result = {}
    for attr in attributes:
        key, value = attr.split(" ", maxsplit=1)
        result[key.strip()] = value.strip('"').strip()
    return result


def parse_gtf_gene_models_format(
    gene_models: GeneModels,
    infile: IO,
    gene_mapping: dict[str, str] | None = None,
    nrows: int | None = None,
) -> bool:
    """Parse GTF gene models file format."""
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
    df = parse_raw(
        infile, expected_columns, nrows=nrows, comment="#")
    if df is None:
        expected_columns.append("comment")
        infile.seek(0)
        df = parse_raw(
            infile, expected_columns, nrows=nrows, comment="#")
        if df is None:
            return False

    if gene_mapping:
        gene_models.alternative_names = copy.deepcopy(gene_mapping)

    records = df.to_dict(orient="records")
    for rec in records:
        feature = rec["feature"]
        if feature == "gene":
            continue
        attributes = _parse_gtf_attributes(rec["attributes"])
        tr_id = attributes["transcript_id"]
        if feature in {"transcript", "Selenocysteine"}:
            if feature == "Selenocysteine" and \
                    tr_id in gene_models.transcript_models:
                continue
            if tr_id in gene_models.transcript_models:
                raise ValueError(
                    f"{tr_id} of {feature} already in transcript models",
                )
            gene = attributes["gene_name"]
            gene = gene_models.alternative_names.get(gene, gene)

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
            gene_models.add_transcript_model(transcript_model)
            continue
        if feature == "exon":
            if tr_id not in gene_models.transcript_models:
                raise ValueError(
                    f"exon or CDS transcript {tr_id} not found "
                    f"in transcript models",
                )
            transcript_model = gene_models.transcript_models[tr_id]
            if feature == "exon":
                exon = Exon(
                    rec["start"], rec["end"], frame=-1,
                )
                transcript_model.exons.append(exon)
                continue
        if feature in {"UTR", "5UTR", "3UTR", "CDS"}:
            continue
        if feature in {"start_codon", "stop_codon"}:
            transcript_model = gene_models.transcript_models[tr_id]
            cds = transcript_model.cds
            transcript_model.cds = \
                (min(cds[0], rec["start"]), max(cds[1], rec["end"]))
            continue

        raise ValueError(
            f"unknown feature {feature} found in gtf gene models")

    for transcript_model in gene_models.transcript_models.values():
        transcript_model.exons = sorted(
            transcript_model.exons, key=lambda x: x.start)
        transcript_model.update_frames()

    return True


def load_gene_mapping(infile: IO) -> dict[str, str]:
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


SUPPORTED_GENE_MODELS_FILE_FORMATS: set[str] = {
    "default",
    "refflat",
    "refseq",
    "ccds",
    "knowngene",
    "gtf",
    "ucscgenepred",
}


def get_parser(
    fileformat: str,
) -> GeneModelsParser | None:
    """Get gene models parser based on file format."""
    # pylint: disable=too-many-return-statements
    if fileformat == "default":
        return parse_default_gene_models_format
    if fileformat == "refflat":
        return parse_ref_flat_gene_models_format
    if fileformat == "refseq":
        return parse_ref_seq_gene_models_format
    if fileformat == "ccds":
        return parse_ccds_gene_models_format
    if fileformat == "knowngene":
        return parse_known_gene_models_format
    if fileformat == "gtf":
        return parse_gtf_gene_models_format
    if fileformat == "ucscgenepred":
        return parse_ucscgenepred_models_format
    return None


def infer_gene_model_parser(
    gene_models: GeneModels,
    infile: IO,
    file_format: str | None = None,
) -> str | None:
    """Infer gene models file format."""
    if file_format is not None:
        parser = get_parser(file_format)
        if parser is not None:
            return file_format

    logger.info("going to infer gene models file format...")
    inferred_formats = []
    for inferred_format in SUPPORTED_GENE_MODELS_FILE_FORMATS:
        gene_models.reset()
        parser = get_parser(inferred_format)
        if parser is None:
            continue
        try:
            logger.debug("trying file format: %s...", inferred_format)
            infile.seek(0)
            res = parser(gene_models, infile, None, 50)
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


def probe_file_format(gene_models: GeneModels) -> str | None:
    """Probe gene models file format."""
    resource = gene_models.resource
    if not resource.get_type() == "gene_models":
        raise ValueError(
            f"unexpected type of genomic resource: {resource.get_type()} "
            f"for {resource.resource_id}")

    filename = resource.get_config()["filename"]
    logger.debug("checing gene models %s file format", filename)
    compression = False
    if filename.endswith(".gz"):
        compression = True
    with resource.open_raw_file(
            filename, mode="rt", compression=compression) as infile:

        return infer_gene_model_parser(gene_models, infile)


def load_gene_models(gene_models: GeneModels) -> GeneModels:
    """Load gene models."""
    resource = gene_models.resource

    filename = resource.get_config()["filename"]
    fileformat = resource.get_config().get("format", None)
    gene_mapping_filename = resource.get_config().get(
        "gene_mapping", None)
    gene_mapping = None
    if gene_mapping_filename is not None:
        compression = False
        if gene_mapping_filename.endswith(".gz"):
            compression = True
        with resource.open_raw_file(
                gene_mapping_filename, "rt",
                compression=compression) as gene_mapping_file:
            logger.debug(
                "loading gene mapping from %s", gene_mapping_filename)
            gene_mapping = load_gene_mapping(gene_mapping_file)

    logger.debug("loading gene models %s (%s)", filename, fileformat)
    compression = False

    if filename.endswith(".gz"):
        compression = True
    with resource.open_raw_file(
            filename, mode="rt", compression=compression) as infile:

        if fileformat is None:
            fileformat = infer_gene_model_parser(gene_models, infile)
            logger.info("infering gene models file format: %s", fileformat)
            if fileformat is None:
                logger.error(
                    "can't infer gene models file format for "
                    "%s...", resource.resource_id)
                raise ValueError("can't infer gene models file format")

        parser = get_parser(fileformat)
        if parser is None:
            logger.error(
                "Unsupported file format %s for "
                "gene model file %s.", fileformat,
                resource.resource_id)
            raise ValueError

        infile.seek(0)

        if not parser(gene_models, infile, gene_mapping, None):
            raise ValueError(
                f"Failed to parse gene models file {filename} "
                f"with format {fileformat}")
    return gene_models
