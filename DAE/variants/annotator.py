'''
Created on Mar 5, 2018

@author: lubo
'''
from variants.family import FamiliesBase
from variants.vcf_utils import VcfFamily
from variants.allele_frequency import VcfAlleleFrequency


class AlleleFrequencyAnnotator(FamiliesBase):

    def __init__(self, ped_df, vcf, vars_df):
        super(AlleleFrequencyAnnotator, self).__init__()

        self.ped_df = ped_df
        self.vcf = vcf
        self.vcf_vars = vcf.vars
        self.vars_df = vars_df

        self.families_build(ped_df, family_class=VcfFamily)

    def annotate(self):
        print(self.vars_df.head())

        allele_counter = VcfAlleleFrequency(self)
        vars_df = allele_counter.calc_allele_frequencies(
            self.vars_df, self.vcf_vars)
        print(vars_df.head())

        return vars_df
