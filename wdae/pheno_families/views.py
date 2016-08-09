'''
Created on Jul 6, 2016

@author: lubo
'''
from rest_framework.views import APIView
from pheno_families.pheno_filter import PhenoMeasureFilters, StudyFilter,\
    RaceFilter, FamilyFilter
import preloaded
from api.query.wdae_query_variants import prepare_query_dict
from api.default_ssc_study import get_ssc_denovo
from helpers.logger import log_filter, LOGGER
from rest_framework.response import Response
import precompute


class FamilyBase(object):

    def __init__(self):
        self.pheno_measure_filter = PhenoMeasureFilters()
        self.study_filter = StudyFilter()
        self.race_filter = RaceFilter()
        register = preloaded.register.get_register()
        self.pheno_measures_register = register.get('pheno_measures')

    def get_pheno_measure_params(self, data):
        if 'familyPhenoMeasure' not in data:
            return None

        assert 'familyPhenoMeasure' in data
        assert 'familyPhenoMeasureMax' in data
        assert 'familyPhenoMeasureMin' in data

        measure = data['familyPhenoMeasure']
        assert self.pheno_measures_register.has_measure(measure)

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
        assert self.pheno_measures_register.has_measure(measure)
        return measure

    def get_family_race_params(self, data):
        if 'familyRace' not in data:
            return None
        race = data['familyRace']
        del data['familyRace']

        race = race.lower()
        if race == 'all':
            return None

        if race not in RaceFilter.get_races():
            raise ValueError("bad race param: {}".format(race))
        return race

    def get_study_name_param(self, data):
        if 'familyStudies' not in data:
            return None

        study_name = data['familyStudies']
        if study_name not in get_ssc_denovo():
            return None
        return study_name

    def get_study_type_params(self, data):
        if 'familyStudyType' not in data:
            return None

        study_type = data['familyStudyType']
        del data['familyStudyType']

        study_type = study_type.lower()
        if study_type in StudyFilter.STUDY_TYPES:
            return study_type
        return None

    def get_family_ids_params(self, data):
        if 'familyIds' in data:
            family_ids = data['familyIds']
            del data['familyIds']

            if isinstance(family_ids, list):
                family_ids = ','.join(family_ids)
            family_ids = family_ids.strip()
            if family_ids != '':
                family_ids = set(family_ids.split(','))
                if len(family_ids) > 0:
                    return family_ids
        return None


class PhenoFamilyBase(FamilyBase):

    def __init__(self):
        FamilyBase.__init__(self)
        self.pheno_families_precompute = precompute.register.get(
            'pheno_families_precompute')

    def prepare_siblins(self, data):
        return set([])

    def prepare_probands(self, data):
        base_measure = self.get_base_pheno_measure_params(data)
        if base_measure is None:
            raise ValueError("base pheno measure not found in request")

        probands = self.pheno_measure_filter.get_matching_probands(
            base_measure)

        family_pheno_measure = self.get_pheno_measure_params(data)
        if family_pheno_measure is not None:
            probands = self.pheno_measure_filter.filter_matching_probands(
                probands, *family_pheno_measure)

        study_type = self.get_study_type_params(data)
        if study_type is not None:
            probands = self.study_filter.\
                filter_matching_probands_by_study_type(
                    probands, study_type)

        study_name = self.get_study_name_param(data)
        if study_name is not None:
            probands = self.study_filter.filter_matching_probands_by_study(
                probands, study_name)

        family_race = self.get_family_race_params(data)
        if family_race is not None:
            probands = self.race_filter.filter_matching_probands_by_race(
                family_race, probands)

        family_ids = self.get_family_ids_params(data)
        if family_ids:
            probands = self.race_filter.filter_probands_by_family_ids(
                family_ids, probands)

        return probands

    def prepare_families(self, data):
        probands = self.prepare_probands(data)
        return [FamilyFilter.strip_proband_id(p) for p in probands]

    def pheno_counters(self, probands):
        prbs = set(probands)
        male = prbs & self.pheno_families_precompute.probands('M')
        female = prbs & self.pheno_families_precompute.probands('F')
        return {
            'autism': {
                'families': len(probands),
                'male': len(male),
                'female': len(female),
            },
            'unaffected': {
                'families': 0,
                'male': 0,
                'female': 0,
            }
        }


class PhenoFamilyCountersView(APIView, PhenoFamilyBase):

    def __init__(self):
        PhenoFamilyBase.__init__(self)

    def post(self, request):
        data = prepare_query_dict(request.data)
        LOGGER.info(log_filter(
            request, "pheno family counters request: " +
            str(data)))

        probands = self.prepare_probands(data)
        result = self.pheno_counters(probands)
        return Response(result)


class FamilyFilterStudies(APIView):

    def get(self, request):
        result = ["All"]
        result.extend(get_ssc_denovo().split(','))
        return Response(result)
