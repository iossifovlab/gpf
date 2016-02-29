'''
Created on Feb 29, 2016

@author: lubo
'''
import preloaded
from families.merge_query import merge_family_ids


def prepare_pheno_measure_query(data, family_ids=None):
    if 'phenoMeasure' not in data:
        return family_ids

    assert 'phenoMeasure' in data
    assert 'phenoMeasureMax' in data
    assert 'phenoMeasureMin' in data

    register = preloaded.register.get_register()
    assert register.has_key('pheno_measures')  # @IgnorePep8

    pheno_measure = data['phenoMeasure']
    pheno_measure_min = data['phenoMeasureMin']
    pheno_measure_max = data['phenoMeasureMax']

    del data['phenoMeasure']
    del data['phenoMeasureMin']
    del data['phenoMeasureMax']

    measures = register.get('pheno_measures')
    assert measures.has_measure(pheno_measure)

    result = measures.get_measure_families(
        pheno_measure,
        float(pheno_measure_min),
        float(pheno_measure_max))

    result = set([str(fid) for fid in result])
    assert isinstance(result, set)

    return merge_family_ids(result, family_ids)
