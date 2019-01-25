#!/usr/bin/env python

from __future__ import absolute_import
import os
import GenomeAccess
from GeneModelFiles import load_gene_models
from variant_annotation.annotator import VariantAnnotator
from annotation.tools.annotator_base import VariantAnnotatorBase


class EffectAnnotator(VariantAnnotatorBase):

    def __init__(self, config):
        super(EffectAnnotator, self).__init__(config)

        self._init_variant_annotation()

        self.effect_type_column = \
            self.config.columns_config.get("effect_type", None)
        self.effect_gene_column = \
            self.config.columns_config.get("effect_gene", None)
        self.effect_details_column = \
            self.config.columns_config.get("effect_details", None)

    def _init_variant_annotation(self):
        genome = None
        if self.config.options.Graw is None:
            from DAE import genomesDB as genomes_db
            genome = genomes_db.get_genome()
        else:
            assert self.config.options.Graw is not None
            assert os.path.exists(self.config.options.Graw)
            genome = GenomeAccess.openRef(self.config.options.Graw)

        assert genome is not None

        # assert self.config.options.Graw is not None
        # assert os.path.exists(self.config.options.Graw)
        gene_models = None
        if self.config.options.Traw is None:
            from DAE import genomesDB as genomes_db
            gene_models = genomes_db.get_gene_models()
        else:
            assert os.path.exists(self.config.options.Traw)
            gene_models = load_gene_models(self.config.options.Traw)
        assert gene_models is not None

        if self.config.options.prom_len is None:
            self.config.options.prom_len = 0
        self.annotation_helper = VariantAnnotator(
            genome, gene_models, promoter_len=self.config.options.prom_len)

    def collect_annotator_schema(self, schema):
        super(EffectAnnotator, self).collect_annotator_schema(schema)
        if self.effect_type_column:
            schema.create_column(self.effect_type_column, 'list(str)')
        if self.effect_gene_column:
            schema.create_column(self.effect_gene_column, 'list(str)')
        if self.effect_details_column:
            schema.create_column(self.effect_details_column, 'list(str)')

    def _not_found(self, aline):
            aline[self.effect_type_column] = ''
            aline[self.effect_gene_column] = ''
            aline[self.effect_details_column] = ''

    def do_annotate(self, aline, variant):
        if variant is None:
            self._not_found(aline)
            return

        assert variant is not None

        try:
            effects = self.annotation_helper.do_annotate_variant(
                chrom=variant.chromosome,
                position=variant.position,
                ref=variant.reference,
                alt=variant.alternative)
            effect_type, effect_gene, effect_details = \
                self.annotation_helper.effect_description1(effects)
            aline[self.effect_type_column] = effect_type
            aline[self.effect_gene_column] = effect_gene
            aline[self.effect_details_column] = effect_details

        except ValueError:
            pass
            # aline.columns[self.effect_type_column] = None
            # aline.columns[self.effect_gene_column] = None
            # aline.columns[self.effect_details_column] = None
