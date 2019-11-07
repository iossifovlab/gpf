'''
Created on Feb 7, 2018

@author: lubo
'''
import os

from cyvcf2 import VCF

import numpy as np
import pandas as pd

from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.pedigrees.family import FamiliesData, Family

from dae.backends.configure import Configure
from dae.backends.vcf.annotate_allele_frequencies import \
    VcfAlleleFrequencyAnnotator
from dae.backends.vcf.raw_vcf import RawVcfVariants

# from variants.parquet_io import save_summary_to_parquet,\
#     read_summary_from_parquet


class VCFVariantWrapper(object):
    def __init__(self, v):
        self.v = v
        gt = np.array(v.genotypes, dtype=np.int8)
        gt = gt[:, 0:2]
        self.gt = gt.T

    def __getattr__(self, name):
        return getattr(self.v, name)


class VCFWrapper(object):

    def __init__(self, filename, region=None):
        self.vcf_file = filename
        self.vcf = VCF(filename, lazy=True)
        self._samples = None
        self._vars = None
        self.region = region

    @property
    def samples(self):
        if self._samples is None:
            self._samples = np.array(self.vcf.samples)
        return self._samples

    @property
    def seqnames(self):
        return self.vcf.seqnames

    @property
    def vars(self):
        if self._vars is None:
            if self.region:
                self._vars = list(
                    map(VCFVariantWrapper, self.vcf(self.region)))
            else:
                self._vars = list(
                    map(VCFVariantWrapper, self.vcf))
        return self._vars


class VcfFamily(Family):

    @classmethod
    def from_df(cls, family_id, ped_df):
        assert 'sampleIndex' in ped_df.columns
        family = Family.from_df(family_id, ped_df)

        family.samples = ped_df['sampleIndex'].values

        return family

    def __init__(self, family_id):
        super(VcfFamily, self).__init__(family_id)
        self.samples = []
        self.alleles = []

    def vcf_samples_index(self, person_ids):
        return self.ped_df[
            self.ped_df['personId'].isin(set(person_ids))
        ]['sampleIndex'].values


class RawVariantsLoader(object):
    SEP1 = '!'
    SEP2 = '|'
    SEP3 = ':'

    def __init__(self, config, genomes_db):
        self.config = config
        self.genomes_db = genomes_db

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
    def has_annotation_file(annotation):
        return os.path.exists(annotation)

    @classmethod
    def load_annotation_file(cls, filename, sep='\t', storage='csv'):
        assert os.path.exists(filename)
        assert storage == 'csv'
        if storage == 'csv':
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
        # elif storage == 'parquet':
        #     annot_df = read_summary_from_parquet(filename)
        #     return annot_df
        else:
            raise ValueError("unexpected input format: {}".format(storage))

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

    @staticmethod
    def load_vcf(filename, region=None):
        assert os.path.exists(filename)
        return VCFWrapper(filename, region)

    # def load_annotation(self, storage='csv'):
    #     assert self.config.annotation

    #     if self.has_annotation_file(self.config.annotation):
    #         return self.load_annotation_file(
    #             self.config.annotation, storage=storage)
    #     else:
    #         # TODO: add test for this
    #         from .builder import variants_builder
    #         variants_builder(self.config.prefix, self.genomes_db)
    #         return self.load_annotation_file(
    #             self.config.annotation, storage=storage)

    @staticmethod
    def _match_pedigree_to_samples(ped_df, vcf):
        vcf_samples = list(vcf.samples)
        samples_needed = set(vcf_samples)
        pedigree_samples = set(ped_df['sample_id'].values)
        missing_samples = samples_needed.difference(pedigree_samples)

        samples_needed = samples_needed.difference(missing_samples)
        assert samples_needed.issubset(pedigree_samples)

        pedigree = []
        seen = set()
        for record in ped_df.to_dict(orient='record'):
            if record['sample_id'] in samples_needed:
                if record['sample_id'] in seen:
                    continue
                record['sampleIndex'] = vcf_samples.index(record['sample_id'])
                pedigree.append(record)
                seen.add(record['sample_id'])

        assert len(pedigree) == len(samples_needed)

        pedigree_order = list(ped_df['sample_id'].values)
        pedigree = sorted(
            pedigree, key=lambda p: pedigree_order.index(p['sample_id']))

        ped_df = pd.DataFrame(pedigree)
        return ped_df, ped_df['sample_id'].values

    @staticmethod
    def _build_initial_vcf_annotation(families, vcf):
        records = []
        for index, v in enumerate(vcf.vars):
            allele_count = len(v.ALT) + 1
            records.append(
                (v.CHROM, v.start + 1,
                    v.REF, None,
                    index, 0, allele_count))
            for allele_index, alt in enumerate(v.ALT):
                records.append(
                    (v.CHROM, v.start + 1,
                        v.REF, alt,
                        index,
                        allele_index + 1, allele_count
                        ))
        annot_df = pd.DataFrame.from_records(
            data=records,
            columns=[
                'chrom', 'position', 'reference', 'alternative',
                'summary_variant_index',
                'allele_index', 'allele_count',
            ])
        freq_annotator = VcfAlleleFrequencyAnnotator(families, vcf)
        annot_df = freq_annotator.annotate(annot_df)
        return annot_df

    @staticmethod
    def build_raw_vcf(ped_df, vcf, annot_df=None):
        ped_df, vcf_samples = RawVariantsLoader._match_pedigree_to_samples(ped_df, vcf)
        families = FamiliesData.from_pedigree_df(ped_df, family_class=VcfFamily)

        if annot_df is None:
            annot_df = RawVariantsLoader._build_initial_vcf_annotation(families, vcf)

        return RawVcfVariants(families, vcf, annot_df)

    @staticmethod
    def load_raw_vcf_variants(
            ped_filename, vcf_filename,
            annotation_filename=None, region=None):
        ped_df = PedigreeReader.load_pedigree_file(ped_filename)
        vcf = RawVariantsLoader.load_vcf(vcf_filename, region)

        annot_df = None
        if annotation_filename is not None \
                and os.path.exists(annotation_filename):
            annot_df = RawVariantsLoader.load_annotation_file(annotation_filename)
        return RawVariantsLoader.build_raw_vcf(ped_df, vcf, annot_df)

    @staticmethod
    def load_raw_vcf_variants_from_prefix(prefix):
        config = Configure.from_prefix_vcf(prefix).vcf
        return RawVariantsLoader.load_raw_vcf_variants(
            config.pedigree, config.vcf, config.annotation
        )
