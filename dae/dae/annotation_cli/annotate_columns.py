from __future__ import annotations

import sys
import abc
import gzip
import yaml
from dae.annotation.annotatable import Annotatable
from dae.annotation.annotatable import Position
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources import build_genomic_resource_repository


class RecordToAnnotable(abc.ABC):
    @abc.abstractmethod
    def build(self, record: dict[str, str]) -> Annotatable:
        pass


class RecordToPosition(RecordToAnnotable):
    def __init__(self, chrom_column, pos_column):
        self.chrom_column = chrom_column
        self.pos_column = pos_column

    def build(self, record: dict[str, str]) -> Annotatable:
        return Position(record[self.chrom_column],
                        int(record[self.pos_column]))


def cli(args: list[str] = None):
    if not args:
        args = sys.argv[1:]
    in_file_name, pipeline_file_name, out_file_name, grr_file_name = args[:4]

    record_to_annotable = RecordToPosition("chrom", "pos")
    with open(grr_file_name) as grr_file:
        grr = build_genomic_resource_repository(yaml.safe_load(grr_file))
    config = AnnotationPipeline.load_and_parse(pipeline_file_name)
    pipeline = AnnotationPipeline.build(config, grr)
    annotation_attributes = pipeline.annotation_schema.names
    print("DEBUG", annotation_attributes)

    if in_file_name == "-":
        in_file = sys.stdin
    elif in_file_name.endswith(".gz"):
        in_file = gzip.open(in_file_name)
    else:
        in_file = open(in_file_name)

    if out_file_name == "-":
        out_file = sys.stdout
    elif out_file_name.endswith(".gz"):
        out_file = gzip.open(out_file_name, "w")
    else:
        out_file = open(out_file_name, "wt")

    hcs = in_file.readline().strip("\r\n").split("\t")
    print(*(hcs + annotation_attributes), sep="\t", file=out_file)

    for line in in_file:
        cs = line.strip("\n\r").split("\t")
        record = dict(zip(hcs, cs))
        annotabale = record_to_annotable.build(record)
        annotation = pipeline.annotate(annotabale)
        print(*(cs + [str(annotation[attrib])
                      for attrib in annotation_attributes]),
              sep="\t", file=out_file)

    if in_file_name != "-":
        in_file.close()

    if out_file_name != "-":
        out_file.close()


if __name__ == '__main__':
    cli(sys.argv[1:])
