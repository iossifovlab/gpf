#!/usr/bin/env python

from __future__ import absolute_import
import os
import GenomeAccess
from GeneModelFiles import load_gene_models
from variant_annotation.annotator import \
    VariantAnnotator as VariantEffectAnnotator
from annotation.tools.annotator_base import VariantAnnotatorBase
from annotation.tools.schema import Schema


class EffectAnnotator(VariantAnnotatorBase):

    def __init__(self, config, schema):
        super(EffectAnnotator, self).__init__(config, schema)

        self._init_variant_annotation()

        self.effect_type_column = \
            self.config.columns_config.get("effect_type", None)
        self.effect_gene_column = \
            self.config.columns_config.get("effect_gene", None)
        self.effect_details_column = \
            self.config.columns_config.get("effect_details", None)

        if self.effect_type_column:
            self.schema.columns[self.effect_type_column] = \
                    Schema.produce_type('list(str)')
        if self.effect_gene_column:
            self.schema.columns[self.effect_gene_column] = \
                    Schema.produce_type('list(str)')
        if self.effect_details_column:
            self.schema.columns[self.effect_details_column] = \
                    Schema.produce_type('list(str)')

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
        self.annotation_helper = VariantEffectAnnotator(
            genome, gene_models, promoter_len=self.config.options.prom_len)

    def do_annotate(self, aline, variant):
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

        except ValueError as e:
            pass
            # aline.columns[self.effect_type_column] = None
            # aline.columns[self.effect_gene_column] = None
            # aline.columns[self.effect_details_column] = None


# class ColumnOrderAction(argparse.Action):

#     def __call__(self, parser, namespace, values, option_string=None):
#         setattr(namespace, self.dest, values)
#         if not hasattr(namespace, 'order'):
#             namespace.order = []
#         namespace.order.append(self.dest)


# def get_argument_parser():
#     """
#     EffectAnnotator options::

#         usage: annotate_variants.py [-h] [-c C] [-p P] [-x X] [-v V] [-a A]
#                             [-r R] [-t T] [-q Q] [-l L] [-P PROM_LEN] [-H]
#                             [-T T] [--Traw TRAW] [--TrawFormat TRAWFORMAT]
#                             [-G G] [--Graw GRAW] [-I I]
#                             [--effect-type EFFECT_TYPE]
#                             [--effect-gene EFFECT_GENE]
#                             [--effect-details EFFECT_DETAILS]
#                             [infile] [outfile]

#         Program to annotate variants (substitutions & indels & cnvs)

#         positional arguments:
#           infile                path to input file; defaults to stdin
#           outfile               path to output file; defaults to stdout

#         optional arguments:
#           -h, --help            show this help message and exit
#           -c C                  chromosome column number/name
#           -p P                  position column number/name
#           -x X                  location (chr:pos) column number/name
#           -v V                  variant column number/name
#           -a A                  alternative allele (FOR SUBSTITUTIONS ONLY)
#                                 column number/name
#           -r R                  reference allele (FOR SUBSTITUTIONS ONLY)
#                                 column number/name
#           -t T                  type of mutation column number/name
#           -q Q                  seq column number/name
#           -l L                  length column number/name
#           -P PROM_LEN           promoter length
#           -H                    no header in the input file
#           -T T                  gene models ID <RefSeq, CCDS, knownGene>
#           --Traw TRAW           outside gene models file path
#           --TrawFormat TRAWFORMAT
#                                 outside gene models format (refseq, ccds,
#                                 knowngene)
#           -G G                  genome ID
#                                 <GATK_ResourceBundle_5777_b37_phiX174, hg19>
#           --Graw GRAW           outside genome file
#           -I I                  geneIDs mapping file; use None for no gene
#                                 name mapping
#           --effect-type EFFECT_TYPE
#                                 name to use for effect type column
#           --effect-gene EFFECT_GENE
#                                 name to use for effect gene column
#           --effect-details EFFECT_DETAILS
#                                 name to use for effect details column

#     """
#     desc = """Program to annotate variants (substitutions & indels & cnvs)"""
#     parser = argparse.ArgumentParser(description=desc)
#     parser.add_argument(
#         '-c', help='chromosome column number/name', action='store')
#     parser.add_argument(
#         '-p', help='position column number/name', action='store')
#     parser.add_argument(
#         '-x', help='location (chr:pos) column number/name', action='store')
#     parser.add_argument(
#         '-v', help='variant column number/name', action='store')
#     parser.add_argument(
#         '-a', help='alternative allele column number/name', action='store')
#     parser.add_argument(
#         '-r', help='reference allele column number/name', action='store')
#     parser.add_argument(
#         '-t', help='type of mutation column number/name', action='store')
#     parser.add_argument(
#         '-q', help='seq column number/name', action='store')
#     parser.add_argument(
#         '-l', help='length column number/name', action='store')

#     parser.add_argument(
#         '-P', help='promoter length', default=0,
#         action='store', type=int, dest="prom_len")
#     parser.add_argument(
#         '-H', help='no header in the input file',
#         default=False,  action='store_true', dest='no_header')

#     parser.add_argument(
#         '-T', help='gene models ID <RefSeq, CCDS, knownGene>',
#         type=str, action='store')
#     parser.add_argument(
#         '--Traw', help='outside gene models file path',
#         type=str, action='store')
#     parser.add_argument(
#         '--TrawFormat',
#         help='outside gene models format (refseq, ccds, knowngene)',
#         type=str, action='store')

#     parser.add_argument(
#         '-G', help='genome ID <GATK_ResourceBundle_5777_b37_phiX174, hg19> ',
#         type=str, action='store')
#     parser.add_argument(
#         '--Graw', help='outside genome file', type=str, action='store')

#     parser.add_argument(
#         '-I', help='geneIDs mapping file; use None for no gene name mapping',
#         default="default", type=str, action='store')

#     parser.add_argument(
#         '--effect-type', help='name to use for effect type column',
#         type=str, action=ColumnOrderAction)
#     parser.add_argument(
#         '--effect-gene', help='name to use for effect gene column',
#         type=str, action=ColumnOrderAction)
#     parser.add_argument(
#         '--effect-details', help='name to use for effect details column',
#         type=str, action=ColumnOrderAction)

#     return parser

# if __name__ == "__main__":
#     main(get_argument_parser(), EffectAnnotator)
