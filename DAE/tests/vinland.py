#!/bin/env python

from DAE import *
from pheno_tool.tool import PhenoTool
from pheno.pheno_db import PhenoDB

stds = vDB.get_studies('IossifovWE2014')

# phdb = PhenoDB()
# phdb.load()

RR = {}
for msrId in phdb.get_instrument_measures('vineland_ii'):
    msr = phdb.get_measure(msrId)
    if msr.measure_type != "continuous":
        continue
    
    cs = [msrId]

    for rl in ['prb', 'sib']:
        tool = PhenoTool(phdb,stds,roles=[rl],measure_id=msrId)
        # for effT in ['LGDs','missense','synonymous']:
        for effT in ['LGDs']:
            print "working on", msrId,rl,effT, "..."
            res = tool.calc(effect_types=[effT], \
                    present_in_parent=['neither'], \
                    present_in_child=['autism only', 
                                        'autism and unaffected',
                                        'unaffected only'])
            cs.append("%.3f" % res.pvalue)
    RR[msrId] = cs


'''
Thoughts for the speedup
for msrId in phdb.get_instrument_measures('vineland_ii'):
    msr = phdb.get_measure(msrId)
    if msr.measure_type != "continuous":
        continue

    effTs = ['LGDs','missnese','synonymous']    
    gens = {effT:get_genotypes(stds,effectTypes=[effT])}
    cs = [msrId]

    for rl in ['prb', 'sib']:
        tool = PhenoTool(phdb,stds,roles=[rl],measure_id=msrId)
        for effT in ['LGDs','missense','synonymous']:
            print "working on", msrId,rl,effT, "..."
            res = tool.calc(gens[effT])
            cs.append("%.3f" % res.pvalue)


1. VariantType object:
    VT(effectTypes,rarity,genes....)

2. Genotyper 
    personVarinats = Genotyper(stds,VT,roles??)

3. 
    phenoTool.cals(personVariants)
OR
    phenoTool.cals(VR)
    phenoTool.cals(VR(effectTypes=['LGDs')
'''
