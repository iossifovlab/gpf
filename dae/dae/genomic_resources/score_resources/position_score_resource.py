from copy import deepcopy
from typing import List
import logging

from dae.genomic_resources.score_resources.score_resource import \
    GenomicScoresResource
from dae.annotation.tools.utils import handle_chrom_prefix
from dae.configuration.schemas.genomic_score_database import attr_schema, \
    genomic_score_schema

logger = logging.getLogger(__name__)


class PositionScoreResource(GenomicScoresResource):

    @classmethod
    def required_columns(cls):
        return ("chrom", "pos_begin", "pos_end")

    @classmethod
    def get_config_schema(cls):
        cols = cls.required_columns() + ("variant", "reference", "alternative")
        attributes_schemas = {
            attr_name: attr_schema for attr_name in cols
        }
        schema = deepcopy(genomic_score_schema)
        schema.update(attributes_schemas)
        return schema

    def fetch_scores(
            self, chrom: str, position: int, scores: List[str] = None):
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        assert chrom in self.get_all_chromosomes()
        line = self._fetch_lines(chrom, position, position)[0]

        scores = dict()
        for col, val in line.scores.items():
            scores[col] = val

        return scores

    def fetch_scores_agg(
        self, chrom: str, pos_begin: int, pos_end: int,
        scores_aggregators
    ):
        chrom = handle_chrom_prefix(self._has_chrom_prefix, chrom)
        assert chrom in self.get_all_chromosomes()
        score_lines = self.fetch_lines(chrom, pos_begin, pos_end)
        logger.debug(f"score lines found: {score_lines}")

        for line in score_lines:
            logger.debug(
                f"pos_end: {pos_end}; line.pos_end: {line.pos_end}; "
                f"pos_begin: {pos_begin}; line.pos_begin: {line.pos_begin}"
            )
            max_pos_begin = max(line.pos_begin, pos_begin)
            min_pos_end = min(pos_end, line.pos_end)
            count = min_pos_end - max_pos_begin + 1
            if count <= 0:
                continue

            assert count >= 1, count
            scores = dict()
            for col, val in line.scores.items():
                if scores is not None and col not in scores:
                    continue
                scores[col] = val
