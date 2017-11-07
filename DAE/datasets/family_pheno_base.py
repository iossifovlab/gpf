'''
Created on Mar 2, 2017

@author: lubo
'''
import numpy as np
from pheno.common import MeasureType


class FamilyPhenoQueryMixin(object):

    def _select_continous_measure_df(self, measure_id, mmin, mmax, roles=None):
        df = self.pheno_db.get_persons_values_df([measure_id], roles=roles)
        df.dropna(inplace=True)

        mvals = df[measure_id]
        selected = None
        if mmin is not None and mmax is not None:
            selected = df[np.logical_and(mvals >= mmin, mvals < mmax)]
        elif mmin is not None:
            selected = df[mvals >= mmin]
        elif mmax is not None:
            selected = df[mvals <= mmax]
        else:
            selected = df
        return selected

    def get_families_by_measure_continuous(
            self, measure_id, mmin=None, mmax=None, roles=None):
        assert self.pheno_db is not None

        selected = self._select_continous_measure_df(
            measure_id, mmin, mmax, roles=roles)
        return set(selected.family_id.values)

    def get_persons_by_measure_continuous(
            self, measure_id, mmin=None, mmax=None, roles=None):
        assert self.pheno_db is not None

        selected = self._select_continous_measure_df(
            measure_id, mmin, mmax, roles=roles)
        return set(selected.person_id.values)

    def _select_categorical_measure_df(
            self, measure_id, selection, roles=None):

        domain = self.get_measure_domain_categorical(measure_id)
        selection = set(selection)
        assert selection <= domain

        df = self.pheno_db.get_persons_values_df([measure_id], roles=roles)
        df.dropna(inplace=True)

        selected = df[df[measure_id].isin(selection)]
        return selected

    def get_families_by_measure_categorical(
            self, measure_id, selection, roles=None):
        assert self.pheno_db is not None

        selected = self._select_categorical_measure_df(
            measure_id, selection=selection, roles=roles)
        return set(selected.family_id.values)

    def get_measure_domain_categorical(self, measure_id):
        assert self.pheno_db is not None

        m = self.pheno_db.get_measure(measure_id)
        assert m.measure_type == MeasureType.categorical
        return set(m.values_domain.split(','))

    def get_family_pheno_filters(self, safe=True, **kwargs):
        assert self.pheno_db is not None

        pheno_filters = kwargs.get('phenoFilters', None)
        if not pheno_filters:
            return []
        assert isinstance(pheno_filters, list)

        result = []
        for pheno_filter in pheno_filters:
            measure_type = pheno_filter['measureType']
            measure_id = pheno_filter['measure']

            if measure_type == 'continuous':
                family_ids = self._filter_continuous_filter(**pheno_filter)
            elif measure_type == 'categorical':
                family_ids = self._filter_categorical_filter(**pheno_filter)
            elif measure_type == 'studies' and measure_id == 'studyFilter':
                family_ids = self._filter_studies_filter(**pheno_filter)
            elif measure_type == 'studies' and measure_id == 'studyTypeFilter':
                family_ids = self._filter_study_types_filter(**pheno_filter)
            else:
                raise NotImplementedError(
                    "unsupported filter type: {}".format(measure_type))
            result.append(family_ids)
        assert all([
            ff is None or isinstance(ff, set)
            for ff in result
        ])
        result = map(self.get_geno_families, result)

        return filter(lambda ff: isinstance(ff, set), result)

    def _filter_continuous_filter(self, safe=True, **kwargs):
        measure_id = kwargs.get('measure', None)
        measure_type = kwargs.get('measureType', None)
        if safe:
            assert measure_type == 'continuous' or \
                measure_type == MeasureType.continuous
            assert self.pheno_db.has_measure(measure_id)
            m = self.pheno_db.get_measure(measure_id)
            assert m.measure_type == MeasureType.continuous

        role = kwargs.get('role', None)
        if not role:
            roles = None
        else:
            roles = [role]
        mmin = kwargs.get('mmin', None)
        mmax = kwargs.get('mmax', None)

        family_ids = self.get_families_by_measure_continuous(
            measure_id, mmin=mmin, mmax=mmax, roles=roles)
        return family_ids

    def _filter_categorical_filter(self, safe=True, **kwargs):
        measure_id = kwargs.get('measure', None)
        measure_type = kwargs.get('measureType', None)

        if safe:
            assert measure_type == 'categorical' or \
                measure_type == MeasureType.categorical
            assert self.pheno_db.has_measure(measure_id)
            m = self.pheno_db.get_measure(measure_id)
            assert m.measure_type == MeasureType.categorical

        role = kwargs.get('role', None)
        if role is not None:
            roles = [role]
        else:
            roles = None
        selection = kwargs.get('selection', None)

        family_ids = self.get_families_by_measure_categorical(
            measure_id, selection=selection, roles=roles)
        return family_ids

    def _filter_studies_filter(self, safe=True, **kwargs):
        if safe:
            measure_id = kwargs.get('measure', None)
            assert measure_id == 'studyFilter'
            measure_type = kwargs.get('measureType', None)
            assert measure_type == 'studies'

        selection = kwargs.get('selection', None)

        for study in self.studies:
            if study.name == selection[0]:
                return set([family for family in study.families])
        assert False

    def _filter_study_types_filter(self, safe=True, **kwargs):
        if safe:
            measure_id = kwargs.get('measure', None)
            assert measure_id == 'studyTypeFilter'
            measure_type = kwargs.get('measureType', None)
            assert measure_type == 'studies'

        selection = kwargs.get('selection', None)

        denovo_studies = self.get_denovo_studies(studyTypes=selection)
        transmitted_studies = \
            self.get_transmitted_studies(studyTypes=selection)
        family_ids = [familyId
                      for study in denovo_studies + transmitted_studies
                      for familyId in study.families]
        return set(family_ids)
