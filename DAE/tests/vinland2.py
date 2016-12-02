'''
Created on Dec 2, 2016

@author: lubo
'''

from DAE import *
from pheno_tool.tool import *
from pheno_tool.genotype_helper import GenotypeHelper


studies = vDB.get_studies('IossifovWE2014')
genotype_helper = GenotypeHelper(studies)

effect_types = ['LGDs', 'missense', 'nonsynonymous']

genotypes = {}
for et in effect_types:
    variants_type = VT(
        effect_types=[et],
        present_in_parent=['neither'],
        present_in_child=['autism only',
                          'autism and unaffected',
                          'unaffected only']
    )
    persons_variants = genotype_helper.get_persons_variants(variants_type)
    genotypes[et] = persons_variants

result = {}

for measure_id in phdb.get_instrument_measures('vineland_ii'):
    measure = phdb.get_measure(measure_id)
    if measure.measure_type != "continuous":
        continue

    cols = [measure_id]
    for role in ['prb', 'sib']:
        tool = PhenoTool(phdb, studies, roles=[role], measure_id=measure_id)
        for et in effect_types:
            print("working on: {}, {}, {}".format(measure_id, role, et))
            res = tool.calc(genotypes[et])
            cols.append("%.3f" % res.pvalue)
    result[measure_id] = cols
