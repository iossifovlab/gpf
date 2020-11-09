import logging

from dae.variants.attributes import VariantType
from dae.annotation.tools.score_annotator import VariantScoreAnnotatorBase


logger = logging.getLogger(__name__)


class VcfInfoAnnotator(VariantScoreAnnotatorBase):

    def __init__(self, config, genomes_db):
        super(VcfInfoAnnotator, self).__init__(config, genomes_db)
        logger.debug(f"config: {config}")

    def _init_score_file(self):
        super(VcfInfoAnnotator, self)._init_score_file()

        logger.debug(self.score_file.schema.col_names)
        logger.debug(f"variants builder {self.variant_builder}")

    def do_annotate(self, aline, variant, liftover_variants):
        if self.liftover:
            variant = liftover_variants.get(self.liftover)

        if variant is None:
            self._scores_not_found(aline)
            return
        if VariantType.is_cnv(variant.variant_type):
            self._scores_not_found(aline)
            return

        chrom = variant.chromosome
        pos = variant.position
        logger.debug(
            f"{self.score_file.score_filename}: looking for VCF frequency of "
            f"{variant}; {chrom}:{pos};")

        scores = self.score_file.fetch_scores(chrom, pos, pos)
        if not scores:
            self._scores_not_found(aline)
            return

        logger.debug(
            f"scores found: {scores}")

        assert len(scores["REF"]) == len(scores["ALT"])
        refs = scores["REF"]
        alts = scores["ALT"]
        for index, (ref, alt) in enumerate(zip(refs, alts)):
            if variant.reference == ref and variant.alternative == alt:
                for name, output in self.config.columns.items():
                    aline[output] = scores[name][index]
                    logger.debug(
                        f"VCF frequency: aline[{output}]={aline[output]}")
                return
