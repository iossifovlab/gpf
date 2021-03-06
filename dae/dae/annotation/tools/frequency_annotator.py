#!/usr/bin/env python
import logging
from os.path import basename

from dae.variants.attributes import VariantType
from dae.annotation.tools.score_annotator import VariantScoreAnnotatorBase


logger = logging.getLogger(__name__)


class FrequencyAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, config, genomes_db):
        super(FrequencyAnnotator, self).__init__(config, genomes_db)

    def _init_score_file(self):
        super(FrequencyAnnotator, self)._init_score_file()

        self.score_filename_base = basename(self.score_file.score_filename)
        self.variant_col_name = self.score_file.config.columns.variant
        assert self.variant_col_name
        assert self.variant_col_name in self.score_file.schema.col_names, \
            "'{}' not in score file schema! Schema columns: {}".format(
                self.variant_col_name, self.score_file.schema.col_names)
        logger.debug(f"variants builder {self.variant_builder}")

    def collect_annotator_schema(self, schema):
        super(FrequencyAnnotator, self).collect_annotator_schema(schema)

    def do_annotate(self, aline, variant, liftover_variants):
        if self.liftover:
            variant = liftover_variants.get(self.liftover)

        if variant is None:
            self._scores_not_found(aline)
            return
        if VariantType.is_cnv(variant.variant_type):
            self._scores_not_found(aline)
            return
        if self.liftover and liftover_variants.get(self.liftover):
            variant = liftover_variants.get(self.liftover)

        chrom = variant.chromosome
        pos = variant.details.cshl_position
        logger.debug(
            f"{self.score_filename_base}: looking for DAE frequency of "
            f"{variant}; {chrom}:{pos};")

        scores = self.score_file.fetch_scores(chrom, pos, pos)
        if not scores:
            self._scores_not_found(aline)
            return
        variant_detail = variant.details.cshl_variant

        variant_occurrences = scores[self.variant_col_name] \
            .count(variant_detail)
        if variant_occurrences > 0:
            if variant_occurrences > 1:
                logger.warning(
                    f"WARNING {self.score_filename_base}: "
                    f"multiple variant occurrences of {chrom}:{pos} {variant}")

            variant_index = scores[self.variant_col_name].index(variant_detail)
            for native, output in self.config.columns.items():
                # FIXME: this conversion should come from schema
                val = scores[native][variant_index]
                try:
                    if val in set(["", " "]):
                        aline[output] = self.score_file.no_score_value
                    else:
                        aline[output] = float(val)
                    logger.debug(
                        f"DAE frequency: aline[{output}]={aline[output]}")

                except ValueError as ex:
                    logger.error(
                        f"problem with: {output}: {chrom}:{pos} - {val}")
                    logger.error(ex)
                    raise ex
