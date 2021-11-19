from __future__ import annotations

import sys
import abc
import gzip
import argparse
from dae.annotation.annotatable import Annotatable
from dae.annotation.annotatable import Position
from dae.annotation.annotatable import Region
from dae.annotation.annotatable import VCFAllele

from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources import build_genomic_resource_repository


class RecordToAnnotable(abc.ABC):
    @abc.abstractmethod
    def build(self, record: dict[str, str]) -> Annotatable:
        pass


class RecordToPosition(RecordToAnnotable):
    def __init__(self, columns: list[str]):
        self.chrom_column, self.pos_column = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        return Position(record[self.chrom_column],
                        int(record[self.pos_column]))


class RecordToRegion(RecordToAnnotable):
    def __init__(self, columns: list[str]):
        self.chrom_col, self.pos_beg_col, self.pos_end_col = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        return Region(record[self.chrom_col],
                      int(record[self.pos_beg_col]),
                      int(record[self.pos_end_col]))


class RecordToVcfAllele(RecordToAnnotable):
    def __init__(self, columns: list[str]):
        self.chrom_col, self.pos_col, self.ref_col, self.alt_col = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        return VCFAllele(record[self.chrom_col],
                         int(record[self.pos_col]),
                         record[self.ref_col],
                         record[self.alt_col])


class VcfLikeRecordToVcfAllele(RecordToAnnotable):
    def __init__(self, columns: list[str]):
        self.vcf_like_col, = columns

    def build(self, record: dict[str, str]) -> Annotatable:
        chrom, pos, ref, alt = record[self.vcf_like_col].split(":")
        return VCFAllele(chrom, int(pos), ref, alt)


RECORD_TO_ANNOTABALE_CONFIGUATION = {
    ("chrom", "pos_beg", "pos_end"): RecordToRegion,
    ("chrom", "pos", "ref", "alt"): RecordToVcfAllele,
    ("vcf_like",): VcfLikeRecordToVcfAllele,
    ("chrom", "pos"): RecordToPosition
}


def build_record_to_annotatable(parameters: dict[str, str],
                                available_columns: set[str]):
    for columns, record_to_annotabale_class in \
            RECORD_TO_ANNOTABALE_CONFIGUATION.items():
        renamed_columns = [parameters.get(
            f'col_{col}', col) for col in columns]
        all_available = len(
            [cn for cn in renamed_columns if cn not in available_columns]) == 0
        if all_available:
            return record_to_annotabale_class(renamed_columns)


def cli(raw_args: list[str] = None):
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('pipeline', help="The pipeline definition file.")
    parser.add_argument('input', default='-', nargs="?",
                        help="the input column file")
    parser.add_argument('output', default='-', nargs="?",
                        help="the output column file")

    parser.add_argument('-grr', '--grr-file_name', default=None,
                        help="The GRR configuration file")

    all_columns = {col for cols in RECORD_TO_ANNOTABALE_CONFIGUATION.keys()
                   for col in cols}
    for col in all_columns:
        parser.add_argument(f'--col_{col}', default=col,
                            help=f"The column name that stores {col}")

    if not raw_args:
        raw_args = sys.argv[1:]
    args = parser.parse_args(raw_args)

    grr = build_genomic_resource_repository(file_name=args.grr_file_name)
    pipeline = AnnotationPipeline.build(
        pipeline_config_file=args.pipeline,
        grr_repository=grr)

    annotation_attributes = pipeline.annotation_schema.names
    print("DEBUG", annotation_attributes)

    if args.input == "-":
        in_file = sys.stdin
    elif args.input.endswith(".gz"):
        in_file = gzip.open(args.input)
    else:
        in_file = open(args.input)

    if args.output == "-":
        out_file = sys.stdout
    elif args.output.endswith(".gz"):
        out_file = gzip.open(args.output, "w")
    else:
        out_file = open(args.output, "wt")

    hcs = in_file.readline().strip("\r\n").split("\t")
    record_to_annotable = build_record_to_annotatable(vars(args), hcs)
    print(*(hcs + annotation_attributes), sep="\t", file=out_file)

    for line in in_file:
        cs = line.strip("\n\r").split("\t")
        record = dict(zip(hcs, cs))
        annotabale = record_to_annotable.build(record)
        annotation = pipeline.annotate(annotabale)
        print(*(cs + [str(annotation[attrib])
                      for attrib in annotation_attributes]),
              sep="\t", file=out_file)

    if args.input != "-":
        in_file.close()

    if args.output != "-":
        out_file.close()


if __name__ == '__main__':
    cli(sys.argv[1:])
