'''
Created on Aug 25, 2016

@author: lubo
'''
from pheno.precompute.families import PrepareIndividuals,\
    PrepareIndividualsGender, PrepareIndividualsSSCPresent,\
    PrepareIndividualsGenderFromSSC


def recompute_pheno_families_cache():
    p10 = PrepareIndividuals()
    p10.prepare()

    p20 = PrepareIndividualsGender()
    p20.prepare()

    p30 = PrepareIndividualsSSCPresent()
    p30.prepare()

    p40 = PrepareIndividualsGenderFromSSC()
    p40.prepare()


if __name__ == '__main__':

    recompute_pheno_families_cache()
