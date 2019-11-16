import os
import numpy as np
import pandas as pd

from dae.variants.family_variant import FamilyVariant

from dae.backends.raw.raw_variants import TransmissionType


class VariantsLoader:

    def __init__(self, families, transmission_type):
        self.families = families
        self.transmission_type = transmission_type

    def summary_genotypes_iterator(self):
        raise NotImplementedError()

    def full_variants_iterator(self, summary_genotypes_iterator=None):
        if summary_genotypes_iterator is None:
            summary_genotypes_iterator = self.summary_genotypes_iterator()

        for summary_variant, family_genotypes in summary_genotypes_iterator:

            family_variants = []
            for fam in self.families.families_list():
                fam_df = fam.ped_df
                gt = family_genotypes[0:2, fam_df.samples_index]
                assert gt.shape == (2, len(fam))

                family_variants.append(FamilyVariant.from_summary_variant(
                    summary_variant, fam, gt))
            yield summary_variant, family_variants

    def family_variants_iterator(self, summary_genotypes_iterator=None):
        for _, fvs in self.full_variants_iterator(
                summary_genotypes_iterator=summary_genotypes_iterator):
            for fv in fvs:
                yield fv


class AlleleFrequencyDecorator(VariantsLoader):
    COLUMNS = [
        'af_parents_called_count',
        'af_parents_called_percent',
        'af_allele_count',
        'af_allele_freq',
    ]

    def __init__(self, variants_loader):
        super(AlleleFrequencyDecorator, self).__init__(
            variants_loader.families,
            TransmissionType.transmitted
        )
        self.variants_loader = variants_loader

        self.independent = self.families.persons_without_parents()
        self.independent_index = \
            np.array(sorted([p.sample_index for p in self.independent]))
        self.n_independent_parents = len(self.independent)

    def get_vcf_variant(self, allele):
        return self.vcf.vars[allele['summary_variant_index']]

    def get_variant_full_genotype(self, family_genotypes):
        gt = family_genotypes
        gt = gt[:, self.independent_index]

        unknown = np.any(gt == -1, axis=0)
        gt = gt[0:2, np.logical_not(unknown)]
        return gt

    def annotate_summary_variant(self, summary_variant, family_genotypes):
        gt = self.get_variant_full_genotype(family_genotypes)
        n_independent_parents = self.n_independent_parents

        n_parents_called = gt.shape[1]
        percent_parents_called = \
            (100.0 * n_parents_called) / n_independent_parents

        for allele in summary_variant.alleles:

            allele_index = allele['allele_index']
            n_alleles = np.sum(gt == allele_index)
            allele_freq = 0.0
            if n_parents_called > 0:
                allele_freq = \
                    (100.0 * n_alleles) / (2.0 * n_parents_called)

            freq = {
                'af_parents_called_count': n_parents_called,
                'af_parents_called_percent': percent_parents_called,
                'af_allele_count': n_alleles,
                'af_allele_freq': allele_freq,
            }
            allele.update_attributes(freq)
        return summary_variant

    def summary_genotypes_iterator(self):
        for summary_variant, family_genotypes in \
                self.variants_loader.summary_genotypes_iterator():

            summary_variant = self.annotate_summary_variant(
                summary_variant, family_genotypes)
            yield summary_variant, family_genotypes


class AnnotationPipelineDecorator(VariantsLoader):

    def __init__(self, variants_loader, annotation_pipeline):
        super(AnnotationPipelineDecorator, self).__init__(
            variants_loader.families,
            TransmissionType.transmitted
        )
        self.variants_loader = variants_loader
        self.annotation_pipeline = annotation_pipeline

    def summary_genotypes_iterator(self):
        for summary_variant, family_genotypes in \
                self.variants_loader.summary_genotypes_iterator():

            self.annotation_pipeline.annotate_summary_variant(summary_variant)
            yield summary_variant, family_genotypes


class RawVariantsLoader:

    SEP1 = '!'
    SEP2 = '|'
    SEP3 = ':'

    @staticmethod
    def convert_array_of_strings(token):
        if not token:
            return None
        token = token.strip()
        words = [w.strip() for w in token.split(RawVariantsLoader.SEP1)]
        return words

    @staticmethod
    def convert_string(token):
        if not token:
            return None
        return token

    @staticmethod
    def _build_annotation_filename(filename):
        return "{}-eff.txt".format(os.path.splitext(filename)[0])

    @staticmethod
    def has_annotation_file(annotation_filename):
        return os.path.exists(annotation_filename)

    @classmethod
    def load_annotation_file(cls, filename, sep='\t'):
        assert os.path.exists(filename)
        with open(filename, 'r') as infile:
            annot_df = pd.read_csv(
                infile, sep=sep, index_col=False,
                dtype={
                    'chrom': str,
                    'position': np.int32,
                },
                converters={
                    'cshl_variant': cls.convert_string,
                    'effect_gene_genes':
                    cls.convert_array_of_strings,
                    'effect_gene_types':
                    cls.convert_array_of_strings,
                    'effect_details_transcript_ids':
                    cls.convert_array_of_strings,
                    'effect_details_details':
                    cls.convert_array_of_strings,
                },
                encoding="utf-8"
            )
        for col in ['alternative', 'effect_type']:
            annot_df[col] = annot_df[col].astype(object). \
                where(pd.notnull(annot_df[col]), None)
        return annot_df

    @staticmethod
    def save_annotation_file(annot_df, filename, sep="\t"):
        def convert_array_of_strings_to_string(a):
            if not a:
                return None
            return RawVariantsLoader.SEP1.join(a)

        vars_df = annot_df.copy()
        vars_df['effect_gene_genes'] = vars_df['effect_gene_genes'].\
            apply(convert_array_of_strings_to_string)
        vars_df['effect_gene_types'] = vars_df['effect_gene_types'].\
            apply(convert_array_of_strings_to_string)
        vars_df['effect_details_transcript_ids'] = \
            vars_df['effect_details_transcript_ids'].\
            apply(convert_array_of_strings_to_string)
        vars_df['effect_details_details'] = \
            vars_df['effect_details_details'].\
            apply(convert_array_of_strings_to_string)
        vars_df.to_csv(
            filename,
            index=False,
            sep=sep
        )
