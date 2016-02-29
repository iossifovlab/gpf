'''
Created on Feb 29, 2016

@author: lubo
'''
import preloaded
from families.merge_query import family_query_merge


def prepare_pheno_measure_query(data):
    if 'phenoMeasure' not in data:
        return data

    assert 'phenoMeasure' in data
    assert 'phenoMeasureMax' in data
    assert 'phenoMeasureMin' in data

    register = preloaded.register.get_register()
    assert register.has_key('pheno_measures')  # @IgnorePep8

    pheno_measure = data['phenoMeasure']
    pheno_measure_min = data['phenoMeasureMin']
    pheno_measure_max = data['phenoMeasureMax']

    measures = register.get('pheno_measures')
    assert measures.has_measure(pheno_measure)

    family_ids = measures.get_measure_families(
        pheno_measure,
        float(pheno_measure_min),
        float(pheno_measure_max))

    family_ids = set([str(fid) for fid in family_ids])

    data = family_query_merge(data, family_ids)
    return data
