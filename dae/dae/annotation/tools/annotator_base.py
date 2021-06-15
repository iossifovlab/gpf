import logging

from copy import deepcopy
from itertools import chain

logger = logging.getLogger(__name__)


class Annotator:

    def __init__(self, config, genomes_db, liftover=None):
        self.config = config
        self.genomes_db = genomes_db

        # FIXME Reintroduce Graw, Traw and TrawFormat?

        self.genomic_sequence = self.genomes_db.load_genomic_sequence(
            # config.options.Graw
        )
        self.gene_models = self.genomes_db.load_gene_models(
            # config.options.Traw, config.options.TrawFormat
        )

        assert self.genomes_db is not None
        assert self.genomic_sequence is not None
        assert self.gene_models is not None

        self.liftover = liftover

    @staticmethod
    def required_columns():
        raise NotImplementedError()

    @property
    def output_columns(self):
        raise NotImplementedError()

    def do_annotate(self, attributes, variant, liftover_variants):
        raise NotImplementedError()

    def annotate_summary_variant(self, summary_variant, liftover_variants):
        for alt_allele in summary_variant.alt_alleles:
            attributes = deepcopy(alt_allele.attributes)
            liftover_variants = {}
            self.do_annotate(attributes, alt_allele, liftover_variants)
            alt_allele.update_attributes(attributes)


class CompositeAnnotator(Annotator):
    def __init__(self, config, genomes_db, liftover=None):
        super().__init__(config, genomes_db, liftover)
        self.annotators = []

    @property
    def output_columns(self):
        return chain(annotator.output_columns for annotator in self.annotators)

    def add_annotator(self, annotator):
        assert isinstance(annotator, Annotator)
        self.annotators.append(annotator)

    def do_annotate(self, aline, variant, liftover_variants):
        try:
            for annotator in self.annotators:
                annotator.do_annotate(aline, variant, liftover_variants)
        except Exception:
            logger.exception(
                f"cant annotate variant {variant}; source line {aline}")
