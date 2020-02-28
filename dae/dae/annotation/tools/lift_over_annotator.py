#!/usr/bin/env python

import gzip

import sys
import os
from pyliftover import LiftOver
from dae.annotation.tools.annotator_base import VariantAnnotatorBase
from dae.annotation.tools.schema import Schema


class LiftOverAnnotator(VariantAnnotatorBase):
    def __init__(self, config, genomes_db):
        super(LiftOverAnnotator, self).__init__(config, genomes_db)

        self.chrom = self.config.options.c
        self.pos = self.config.options.p
        if not self.config.options.vcf:
            self.location = self.config.options.x
        else:
            self.location = None
            assert self.chrom is not None
            assert self.pos is not None

        self.columns = self.config.columns
        assert self.columns.new_x or (
            self.columns.new_c and self.columns.new_p
        )

        self.lift_over = self.build_lift_over(self.config.options.chain_file)

    def collect_annotator_schema(self, schema):
        super(LiftOverAnnotator, self).collect_annotator_schema(schema)
        for key, value in self.columns.field_values_iterator():
            if key == "new_x" or key == "new_c":
                schema.columns[value] = Schema.produce_type("str")
            elif key == "new_p":
                schema.columns[value] = Schema.produce_type("str")

    @staticmethod
    def build_lift_over(chain_filename):
        assert chain_filename is not None
        assert os.path.exists(chain_filename)

        chain_file = gzip.open(chain_filename, "r")
        return LiftOver(chain_file)

    def do_annotate(self, aline, variant):
        if self.location and self.location in aline:
            location = aline[self.location]
            chrom, pos = location.split(":")
            pos = int(pos)
        else:
            chrom = aline[self.chrom]
            pos = int(aline[self.pos])

        # positions = [int(p) - 1 for p in position.split('-')]
        liftover_pos = pos - 1
        converted_coordinates = self.lift_over.convert_coordinate(
            chrom, liftover_pos
        )

        if converted_coordinates is None:
            print(
                "position: chrom=",
                chrom,
                "; pos=",
                pos,
                "(0-pos=",
                liftover_pos,
                ")",
                "can not be converted into target reference genome",
                file=sys.stderr,
            )
            new_c = None
            new_p = None
            new_x = None

        elif len(converted_coordinates) == 0:
            print(
                "position: chrom=",
                chrom,
                "; pos=",
                pos,
                "(0-pos=",
                liftover_pos,
                ")",
                "can not be converted into target reference genome",
                file=sys.stderr,
            )
            new_c = None
            new_p = None
            new_x = None
        else:
            if len(converted_coordinates) > 1:
                print(
                    "position: chrom=",
                    chrom,
                    "; pos=",
                    pos,
                    "has more than one corresponding position "
                    "into target reference genome",
                    converted_coordinates,
                    file=sys.stderr,
                )

            new_c = converted_coordinates[0][0]
            new_p = converted_coordinates[0][1] + 1
            new_x = "{}:{}".format(new_c, new_p)

        if self.columns.new_x:
            aline[self.columns.new_x] = new_x
        if self.columns.new_c:
            aline[self.columns.new_c] = new_c
        if self.columns.new_p:
            aline[self.columns.new_p] = new_p
