'''
Created on Feb 29, 2016

@author: lubo
'''
import preloaded
from families.merge_query import merge_family_ids


def prepare_pheno_measure_query(data, family_ids=None):
    if 'familyPhenoMeasure' not in data:
        return family_ids

    assert 'familyPhenoMeasure' in data
    assert 'familyPhenoMeasureMax' in data
    assert 'familyPhenoMeasureMin' in data

    register = preloaded.register.get_register()
    assert register.has_key('pheno_measures')  # @IgnorePep8

    pheno_measure = data['familyPhenoMeasure']
    pheno_measure_min = data['familyPhenoMeasureMin']
    pheno_measure_max = data['familyPhenoMeasureMax']

    del data['familyPhenoMeasure']
    del data['familyPhenoMeasureMin']
    del data['familyPhenoMeasureMax']

    measures = register.get('pheno_measures')
    assert measures.has_measure(pheno_measure)

    result = measures.get_measure_families(
        pheno_measure,
        float(pheno_measure_min),
        float(pheno_measure_max))

    result = set([str(fid) for fid in result])
    assert isinstance(result, set)

    return merge_family_ids(result, family_ids)
