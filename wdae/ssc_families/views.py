'''
Created on Jul 8, 2016

@author: lubo
'''
from pheno_families.views import FamilyBase
from ssc_families.ssc_filter import QuadFamiliesFilter, FamiliesGenderFilter


class SSCFamilyBase(FamilyBase):

    def __init__(self):
        FamilyBase.__init__(self)
        self.quad_filter = QuadFamiliesFilter()
        self.families_gender_filter = FamiliesGenderFilter()

    def get_quad_params(self, data):
        if 'familyQuadTrio' in data:
            quad = data['familyQuadTrio'].lower()
            if 'all' == quad:
                return None

            return 'quad'
        return None

    @staticmethod
    def _parse_gender(gender):
        if isinstance(gender, list):
            gender = ','.join(gender)
        if gender.lower() == 'male':
            return 'M'
        if gender.lower() == 'female':
            return 'F'
        return None

    def get_probands_gender_params(self, data):
        if 'familyPrbGender' not in data:
            return None
        gender = self._parse_gender(data['familyPrbGender'])
        return gender

    def get_siblings_gender_params(self, data):
        if 'familySibGender' not in data:
            return None
        gender = self._parse_gender(data['familySibParameters'])
        return gender

    def prepare_families(self, data):
        families = None

        family_pheno_measure = self.get_pheno_measure_params(data)
        if family_pheno_measure is not None:
            families = self.pheno_measure_filter.filter_matching_families(
                families, *family_pheno_measure)

        study_type = self.get_study_type_params(data)
        if study_type is not None:
            families = self.study_filter.\
                filter_matching_families_by_study_type(
                    families, study_type)

        study_name = self.get_study_name_param(data)
        if study_name is not None:
            families = self.study_filter.filter_matching_families_by_study(
                families, study_name)

        family_race = self.get_family_race_params(data)
        if family_race is not None:
            families = self.race_filter.filter_matching_families_by_race(
                family_race, families)

        quad = self.get_quad_params(data)
        if quad is not None:
            families = self.quad_filter.filter_matching_familes(
                families, study_type, study_name)

        prb_gender = self.get_probands_gender_params(data)
        if prb_gender is not None:
            families = self.families_gender_filter.filter_matching_probands(
                families, prb_gender)

        sib_gender = self.get_siblings_gender_params(data)
        if sib_gender is not None:
            families = self.families_gender_filter.filter_matching_siblings(
                families, sib_gender)

        family_ids = self.get_family_ids_params(data)
        if family_ids:
            families = [f for f in families if f in family_ids]

        return families
