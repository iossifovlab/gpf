'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function
import gzip
import os

from cyvcf2 import VCF

import numpy as np
import pandas as pd
import re

from DAE import genomesDB


class VCFWrapper(object):

    def __init__(self, filename):
        self.vcf_file = filename
        self.vcf = VCF(filename)
        self._samples = None

    @property
    def samples(self):
        if self._samples is None:
            self._samples = np.array(self.vcf.samples)
        return self._samples


class StudyLoader(object):

    def __init__(self, study_config):
        self.config = study_config

    def load_summary(self):
        print(self.config.summary)
        assert self.config.summary
        assert os.path.exists(self.config.summary)

        with gzip.GzipFile(self.config.summary, 'r') as infile:
            sum_df = pd.read_csv(
                infile, sep='\t', index_col=False,
                dtype={'chr': str})
        sum_df.drop('familyData', axis=1, inplace=True)
        return sum_df

    def load_pedigree(self):
        assert self.config.pedigree
        assert os.path.exists(self.config.pedigree)

        ped_df = pd.read_csv(self.config.pedigree, sep='\t', index_col=False)
        ped = {}
        for p in ped_df.to_dict(orient='records'):
            ped[p['personId']] = p

        assert len(ped) == len(ped_df)

        return ped_df, ped

    def load_vcf(self):
        assert self.config.vcf
        assert os.path.exists(self.config.vcf)

        return VCFWrapper(self.config.vcf)


SUB_RE = re.compile('^sub\(([ACGT])->([ACGT])\)$')
INS_RE = re.compile('^ins\(([ACGT]+)\)$')
DEL_RE = re.compile('^del\((\d+)\)$')

GA = genomesDB.get_genome()  # @UndefinedVariable


def dae2vcf_variant(chrom, position, var):
    match = SUB_RE.match(var)
    if match:
        return chrom, position, match.group(1), match.group(2)

    match = INS_RE.match(var)
    if match:
        alt_suffix = match.group(1)
        reference = GA.getSequence(chrom, position - 1, position - 1)
        return chrom, position - 1, reference, reference + alt_suffix

    match = DEL_RE.match(var)
    if match:
        count = int(match.group(1))
        reference = GA.getSequence(chrom, position - 1, position + count - 1)
        return chrom, position - 1, reference, reference[0]

    raise NotImplementedError('weird variant: ' + var)


class VcfVariantBase(object):

    def __init__(self, chromosome, position, reference, alternative):
        self.chromosome = chromosome
        self.position = position
        self.reference = reference
        self.alternative = alternative

    def __repr__(self):
        return '{}:{} {}->{}'.format(
            self.chromosome, self.position, self.reference, self.alternative)

    @staticmethod
    def from_dae_variant(chrom, pos, variant):
        chrom, position, ref, alt = dae2vcf_variant(chrom, pos, variant)
        return VcfVariantBase(chrom, position - 1, ref, alt)

    @staticmethod
    def from_vcf_variant(variant):
        assert len(variant.ALT) == 1
        return VcfVariantBase(
            variant.CHROM, variant.start, variant.REF, str(variant.ALT[0]))

    def __eq__(self, other):
        #         print("__eq__ called...")
        #         print("chroms: ", self.chromosome == other.chromosome)
        #         print("pos:    ", self.position == other.position)
        #         print("ref:    ", self.reference == other.reference)
        #         print("alt:    ", self.alternative == other.alternative)

        return self.chromosome == other.chromosome and \
            self.position == other.position and \
            self.reference == other.reference and \
            self.alternative == other.alternative

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return int(self.chromosome) <= int(other.chromosome) and \
            self.position < other.position

    def __gt__(self, other):
        return int(self.chromosome) >= int(other.chromosome) and \
            self.position > other.position


class VariantMatcher(object):

    def __init__(self, study_config):
        self.config = study_config
        self.vars_df = None
        self.vcf_vars = None

    def _run(self):
        loader = StudyLoader(self.config)
        vcf = loader.load_vcf()
        vars_df = loader.load_summary()

        vs_iter = iter(vcf.vcf)
        count = 0
        matched = pd.Series(
            data=np.zeros(len(vars_df), dtype=np.bool),
            index=vars_df.index, dtype=np.bool)

        matched_vcf = []
        for index, row in vars_df.iterrows():
            # print(row)
            v1 = VcfVariantBase.from_dae_variant(
                row['chr'], row['position'], row['variant'])

            variant = next(vs_iter)
            v2 = VcfVariantBase.from_vcf_variant(variant)

            while v1 > v2:
                # print(index, "skipping vcf v2:", v2, "(", v1, ")")
                variant = next(vs_iter)
                v2 = VcfVariantBase.from_vcf_variant(variant)

            if v1 < v2:
                # print(index, "skipping dae v1:", v1, "(", v2, ")")
                continue

            if v1 != v2:
                # print("skipping: postions matched, but not equal: ", v1, v2)
                continue
            # print(index, "matched...", v1, v2)
            count += 1
            matched[index] = True
            matched_vcf.append(variant)

        print("matched variants: ", count)
        vars_df['matched'] = matched
        return vars_df[matched], matched_vcf

    def match(self):
        self.vars_df, self.vcf_vars = self._run()
