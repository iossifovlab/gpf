from builtins import NotImplementedError
import logging

from copy import deepcopy

from dae.configuration.gpf_config_parser import GPFConfigParser

logger = logging.getLogger(__name__)


class AnnotatorBase(object):

    """
    `AnnotatorBase` is base class of all `Annotators`.
    """

    def __init__(self, config, genomes_db, liftover=None):
        self.config = config
        self.genomes_db = genomes_db
        self.genomic_sequence = self.genomes_db.load_genomic_sequence(
            config.options.Graw
        )
        self.gene_models = self.genomes_db.load_gene_models(
            config.options.Traw, config.options.TrawFormat)

        assert self.genomes_db is not None
        assert self.genomic_sequence is not None
        assert self.gene_models is not None

        self.mode = "replace"
        if self.config.options.mode == "replace":
            self.mode = "replace"
        elif self.config.options.mode == "append":
            self.mode = "append"
        elif self.config.options.mode == "overwrite":
            self.mode = "overwrite"

        self.liftover = liftover

    def do_annotate(self, aline, variant, liftover_variants):
        raise NotImplementedError()

    def collect_annotator_schema(self, schema):
        # raise NotImplementedError()
        pass


class CopyAnnotator(AnnotatorBase):
    def __init__(self, config, genomes_db):
        super(CopyAnnotator, self).__init__(config, genomes_db)

    def collect_annotator_schema(self, schema):
        for key, value in self.config.columns.items():
            assert key in schema.columns, [key, schema.columns]
            schema.columns[value] = schema.columns[key]


class VariantAnnotatorBase(AnnotatorBase):
    def __init__(self, config, genomes_db):
        super(VariantAnnotatorBase, self).__init__(config, genomes_db)

        if not self.config.virtual_columns:
            self.config = GPFConfigParser.modify_tuple(
                self.config,
                {
                    "virtual_columns": [
                        "CSHL_location",
                        "CSHL_chr",
                        "CSHL_position",
                        "CSHL_variant",
                        "VCF_chr",
                        "VCF_position",
                        "VCF_ref",
                        "VCF_alt",
                    ]
                },
            )

    def collect_annotator_schema(self, schema):
        for vcol in self.config.virtual_columns:
            if "position" in vcol:
                schema.create_column(vcol, "int")
            else:
                schema.create_column(vcol, "str")

    def annotate_summary_variant(self, summary_variant, liftover_variants):
        for alt_allele in summary_variant.alt_alleles:
            attributes = deepcopy(alt_allele.attributes)
            liftover_variants = {}
            self.do_annotate(attributes, alt_allele, liftover_variants)
            alt_allele.update_attributes(attributes)


class CompositeVariantAnnotator(VariantAnnotatorBase):
    def __init__(self, config, genomes_db):
        super(CompositeVariantAnnotator, self).__init__(config, genomes_db)
        self.annotators = []

    def add_annotator(self, annotator):
        assert isinstance(annotator, VariantAnnotatorBase)
        self.annotators.append(annotator)

    def do_annotate(self, aline, variant, liftover_variants):
        try:
            for annotator in self.annotators:
                annotator.do_annotate(aline, variant, liftover_variants)
        except Exception:
            logger.exception(
                f"cant annotate variant {variant}; source line {aline}")

    def collect_annotator_schema(self, schema):
        super(CompositeVariantAnnotator, self).collect_annotator_schema(schema)
        for annotator in self.annotators:
            annotator.collect_annotator_schema(schema)
