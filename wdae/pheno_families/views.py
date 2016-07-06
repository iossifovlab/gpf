'''
Created on Jul 6, 2016

@author: lubo
'''
from rest_framework.views import APIView
from pheno_families.pheno_filter import PhenoMeasureFilters, PhenoStudyFilter,\
    PhenoRaceFilter
import preloaded
from api.query.wdae_query_variants import prepare_query_dict


class PhenoFamilyView(APIView):

    def __init__(self):
        self.pheno_measure_filter = PhenoMeasureFilters()
        self.study_filter = PhenoStudyFilter()
        self.race_filter = PhenoRaceFilter()
        register = preloaded.register.get_register()
        self.pheno_measures_regiser = register.get('pheno_measures')

    def get_pheno_measure_params(self, data):
        if 'familyPhenoMeasure' not in data:
            return None

        assert 'familyPhenoMeasure' in data
        assert 'familyPhenoMeasureMax' in data
        assert 'familyPhenoMeasureMin' in data

        measure = data['familyPhenoMeasure']
        assert self.pheno_measures_register.has_key(measure)  # @IgnorePep8

        measure_min = data['familyPhenoMeasureMin']
        measure_max = data['familyPhenoMeasureMax']

        del data['familyPhenoMeasure']
        del data['familyPhenoMeasureMin']
        del data['familyPhenoMeasureMax']

        return (measure, float(measure_min), float(measure_max))

    def get_base_pheno_measure_params(self, data):
        if 'phenoMeasure' not in data:
            return None
        measure = data['phenoMeasure']
        assert self.pheno_measures_regiser.has_measure(measure)
        return measure

    def get_family_race_params(self, data):
        if 'familyRace' not in data:
            return None
        race = data['familyRace']
        del data['familyRace']

        race = race.lower()
        if race not in PhenoRaceFilter.get_races():
            return None
        return race

    def prepare(self, data):
        data = prepare_query_dict(data)

    def post(self, request):
        pass
