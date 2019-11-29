import os
import numpy as np
import pandas as pd

from dae.pedigrees.family import FamiliesData
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant

from dae.backends.raw.raw_variants import TransmissionType


class FamiliesGenotypes:
    def __init__(self):
        pass

    def full_families_genotypes(self):
        raise NotImplementedError()

    def get_family_genotype(self, family_id):
        raise NotImplementedError()

    def family_genotype_iterator(self):
        raise NotImplementedError()


class VariantsLoader:

    def __init__(self, families, transmission_type, params={}):
        assert isinstance(families, FamiliesData)
        self.families = families
        self.transmission_type = transmission_type
        self.params = params

    def summary_genotypes_iterator(self):
        raise NotImplementedError()

    def full_variants_iterator(self, summary_genotypes_iterator=None):
        if summary_genotypes_iterator is None:
            summary_genotypes_iterator = self.summary_genotypes_iterator()

        for summary_variant, family_genotypes in summary_genotypes_iterator:

            family_variants = []
            for fam, gt in family_genotypes.family_genotype_iterator():
                family_variants.append(
                    FamilyVariant.from_summary_variant(
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
        gt = family_genotypes.full_families_genotypes()
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
            variants_loader.transmission_type
        )
        self.variants_loader = variants_loader
        self.annotation_pipeline = annotation_pipeline
        self.annotation_schema = annotation_pipeline.build_annotation_schema()

    def summary_genotypes_iterator(self):
        for summary_variant, family_genotypes in \
                self.variants_loader.summary_genotypes_iterator():

            self.annotation_pipeline.annotate_summary_variant(summary_variant)
            yield summary_variant, family_genotypes


class StoredAnnotationDecorator(VariantsLoader):

    SEP1 = '!'
    SEP2 = '|'
    SEP3 = ':'

    def __init__(self, variants_loader, annotation_filename):
        super(StoredAnnotationDecorator, self).__init__(
            variants_loader.families,
            variants_loader.transmission_type
        )
        self.variants_loader = variants_loader
        assert os.path.exists(annotation_filename)
        self.annotation_filename = annotation_filename

    @staticmethod
    def decorate(variants_loader, source_filename):
        annotation_filename = \
            StoredAnnotationDecorator._build_annotation_filename(
                    source_filename
                )
        if not os.path.exists(annotation_filename):
            return variants_loader
        else:
            variants_loader = StoredAnnotationDecorator(
                variants_loader,
                annotation_filename
            )
            return variants_loader

    @classmethod
    def _convert_array_of_strings(cls, token):
        if not token:
            return None
        token = token.strip()
        words = [w.strip() for w in token.split(cls.SEP1)]
        return words

    @staticmethod
    def _convert_string(token):
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
                    'cshl_variant': cls._convert_string,
                    'effect_gene_genes':
                    cls._convert_array_of_strings,
                    'effect_gene_types':
                    cls._convert_array_of_strings,
                    'effect_details_transcript_ids':
                    cls._convert_array_of_strings,
                    'effect_details_details':
                    cls._convert_array_of_strings,
                },
                encoding="utf-8"
            )
        for col in ['alternative', 'effect_type']:
            annot_df[col] = annot_df[col].astype(object). \
                where(pd.notnull(annot_df[col]), None)
        return annot_df

    @classmethod
    def save_annotation_file(cls, annot_df, filename, sep="\t"):
        def convert_array_of_strings_to_string(a):
            if not a:
                return None
            return cls.SEP1.join(a)

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

    def summary_genotypes_iterator(self):
        variant_iterator = self.variants_loader.summary_genotypes_iterator()

        annot_df = self.load_annotation_file(self.annotation_filename)
        for index, group_df in annot_df.groupby('summary_variant_index'):
            sv, family_genotypes = next(variant_iterator)

            assert index == \
                sv.ref_allele.get_attribute('summary_variant_index')

            records = group_df.to_dict(orient='records')
            summary_variant = SummaryVariantFactory.\
                summary_variant_from_records(
                    records,
                    transmission_type=self.transmission_type)

            yield summary_variant, family_genotypes
