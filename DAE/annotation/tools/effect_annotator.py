#!/usr/bin/env python

from __future__ import absolute_import
import os
from collections import OrderedDict

import GenomeAccess
from GeneModelFiles import load_gene_models
from variant_annotation.annotator import VariantAnnotator
from annotation.tools.annotator_base import VariantAnnotatorBase


class EffectAnnotatorBase(VariantAnnotatorBase):
    COLUMNS_SCHEMA = [
        ('effect_type', 'list(str)'),
        ('effect_gene', 'list(str)'),
        ('effect_details', 'list(str)'),
    ]

    def __init__(self, config):
        super(EffectAnnotatorBase, self).__init__(config)

        self._init_variant_annotation()
        self.columns = OrderedDict()
        for col_name, col_type in self.COLUMNS_SCHEMA:
            self.columns[col_name] = \
                self.config.columns_config.get(col_name, None)

    def collect_annotator_schema(self, schema):
        super(EffectAnnotatorBase, self).collect_annotator_schema(schema)
        for col_name, col_type in self.COLUMNS_SCHEMA:
            if self.columns.get(col_name, None):
                schema.create_column(col_name, col_type)

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

    def _not_found(self, aline):
        for col_name, col_conf in self.columns.items():
            if col_conf:
                aline[col_conf] = ''

    def do_annotate(self, aline, variant):
        raise NotImplementedError()


class EffectAnnotator(EffectAnnotatorBase):

    COLUMNS_SCHEMA = [
        ('effect_type', 'list(str)'),
        ('effect_gene', 'list(str)'),
        ('effect_details', 'list(str)'),
    ]

    def __init__(self, config):
        super(EffectAnnotator, self).__init__(config)

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

            aline[self.columns['effect_type']] = effect_type
            aline[self.columns['effect_gene']] = effect_gene
            aline[self.columns['effect_details']] = effect_details

        except ValueError:
            pass
