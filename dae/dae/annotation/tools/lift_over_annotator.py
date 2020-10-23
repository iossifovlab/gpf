#!/usr/bin/env python

import gzip

import sys
import os
import logging

from pyliftover import LiftOver
from dae.annotation.tools.annotator_base import VariantAnnotatorBase
from dae.annotation.tools.schema import Schema


logger = logging.getLogger(__name__)


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

        self.strand = self.config.options.get("s")

        self.columns = self.config.columns
        assert self.columns.new_x or (
            self.columns.new_c and self.columns.new_p
        )
        logger.debug(
            f"columns: chrom={self.chrom}; pos={self.pos}; "
            f"strand={self.strand}")
        logger.info(
            f"new columns are: {self.columns}")

        self.lift_over = self.build_lift_over(self.config.options.chain_file)

        logger.debug(
            f"creating liftover annotation: {self.config.options.chain_file}")

    def collect_annotator_schema(self, schema):
        super(LiftOverAnnotator, self).collect_annotator_schema(schema)
        for key, value in self.columns.items():
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
        liftover_pos = None
        if self.location and self.location in aline:
            location = aline[self.location]
            chrom, pos = location.split(":")
            pos = int(pos)
            liftover_pos = pos - 1
        else:
            chrom = aline[self.chrom]
            pos = aline[self.pos]
            if pos is not None:
                pos = int(pos)
                liftover_pos = pos - 1
        strand = aline.get(self.strand, "+")

        if liftover_pos is None:
            logger.info(
                f"source liftover position is {liftover_pos}; "
                f"can't liftover...")
            return

        # positions = [int(p) - 1 for p in position.split('-')]
        converted_coordinates = self.lift_over.convert_coordinate(
            chrom, liftover_pos, strand)

        logger.debug(
            f"source coordinates: {chrom}:{liftover_pos}, {strand}; "
            f"liftover corrdinates ({len(converted_coordinates)}): "
            f"{converted_coordinates}")

        if converted_coordinates is None:
            logger.info(
                f"position: chrom={chrom}; pos={pos}, (0-pos={liftover_pos}) "
                f"can not be converted into target reference genome")
            new_c = None
            new_p = None
            new_x = None
            new_s = None

        elif len(converted_coordinates) == 0:
            logger.info(
                f"position: chrom={chrom}; pos={pos}, (0-pos={liftover_pos})"
                f"can not be converted into target reference genome")
            new_c = None
            new_p = None
            new_x = None
            new_s = None
        else:
            if len(converted_coordinates) > 1:
                logger.info(
                    f"position: chrom={chrom}; pos={pos}; "
                    f"can not be converted into target reference genome; "
                    f"has more than one corresponding position "
                    f"into target reference genome {converted_coordinates}")

            new_c = converted_coordinates[0][0]
            new_p = converted_coordinates[0][1] + 1
            new_s = converted_coordinates[0][2]
            new_x = "{}:{}".format(new_c, new_p)

            # logger.debug(
            #     f"liftover source position: {chrom}:{pos} -> "
            #     f"after litfover: "
            #     f"{new_c}:{new_p}; (location {new_x})")

        if self.columns.new_x:
            aline[self.columns.new_x] = new_x
        if self.columns.new_c:
            aline[self.columns.new_c] = new_c
        if self.columns.new_p:
            aline[self.columns.new_p] = new_p
        if self.columns.new_s:
            aline[self.columns.new_s] = new_s
