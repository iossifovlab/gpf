'''
Created on Feb 7, 2018

@author: lubo
'''
import os

from cyvcf2 import VCF

import numpy as np
import pandas as pd

from dae.pedigrees.family import FamiliesData, Family

from dae.backends.raw.loader import RawVariantsLoader

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


class RawVcfLoader(RawVariantsLoader):

    @staticmethod
    def load_vcf_file(filename, region=None):
        assert os.path.exists(filename)
        return VCFWrapper(filename, region)

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
                        allele_index + 1, allele_count)
                )
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

    @classmethod
    def build_raw_vcf(cls, ped_df, vcf, annot_df=None):
        ped_df, vcf_samples = cls._match_pedigree_to_samples(ped_df, vcf)
        families = FamiliesData.from_pedigree_df(
            ped_df, family_class=VcfFamily)

        if annot_df is None:
            annot_df = cls._build_initial_vcf_annotation(families, vcf)

        return RawVcfVariants(families, vcf, annot_df)

    @classmethod
    def load_raw_vcf_variants(
            cls, ped_df, vcf_filename,
            annotation_filename=None, region=None):

        vcf = cls.load_vcf_file(vcf_filename, region)

        annot_df = None
        if annotation_filename is None:
            annotation_filename = cls.annotation_filename(vcf_filename)
        if annotation_filename is not None \
                and os.path.exists(annotation_filename):
            annot_df = cls.load_annotation_file(annotation_filename)

        return cls.build_raw_vcf(ped_df, vcf, annot_df)

    @classmethod
    def load_and_annotate_raw_vcf_variants(
            cls, ped_df, vcf_filename,
            annotation_pipeline, region=None):

        fvars = cls.load_raw_vcf_variants(ped_df, vcf_filename, region)
        fvars.annotate(annotation_pipeline)
        return fvars
