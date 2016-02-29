'''
Created on Feb 29, 2016

@author: lubo
'''
import preloaded


class PhenoMeasurePrepare(object):
    """
    "phenoMeasure": "non_verbal_iq"
     "phenoMeasureMax": 161
     "phenoMeasureMin": 9

    """
    @staticmethod
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

        family_ids = [str(fid) for fid in family_ids]

        if 'familyIds' not in data:
            data['familyIds'] = ",".join(family_ids)
        else:
            family_ids = set(family_ids)
            request_family_ids = set(data['familyIds'].split(','))
            result_family_ids = family_ids & request_family_ids
            data['familyIds'] = ",".join(result_family_ids)
        return data
