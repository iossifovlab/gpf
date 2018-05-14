'''
Created on Dec 2, 2016

@author: lubo
'''
from __future__ import print_function

from DAE import *
from pheno_tool.tool import *
from pheno_tool.genotype_helper import GenotypeHelper

# from utils.profiler import profile


# @profile("pheno_tool.prof")
def main():
    studies = vDB.get_studies('IossifovWE2014')
    genotype_helper = GenotypeHelper(studies)

    effect_types = ['LGDs', 'missense', 'nonsynonymous']

    genotypes = {}
    for et in effect_types:
        variants_type = VT(
            effect_types=[et],
            present_in_parent=['neither'],
            present_in_child=['affected only',
                              'affected and unaffected',
                              'unaffected only']
        )
        persons_variants = genotype_helper.get_persons_variants_df(
            variants_type)
        genotypes[et] = persons_variants

    result = {}

    phdb = phenoDB.get_pheno_db('ssc')

    for count, measure_id in enumerate(
            phdb.get_instrument_measures('vineland_ii')):

        measure = phdb.get_measure(measure_id)
        if measure.measure_type != "continuous":
            continue

        cols = [measure_id]
        for role in ['prb', 'sib']:
            tool = PhenoTool(
                phdb, studies, roles=[role], measure_id=measure_id)
            for et in effect_types:
                print("working on: {}, {}, {}".format(measure_id, role, et))
                res = tool.calc(genotypes[et])
                cols.append("%.3f" % res.pvalue)
        result[measure_id] = cols


if __name__ == "__main__":
    main()
