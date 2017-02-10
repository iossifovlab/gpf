'''
Created on Feb 9, 2017

@author: lubo
'''
from DAE import pheno, vDB
import itertools
from query_variants import generate_response
from common.query_base import QueryBase


# class AllFilter(object):
#
#     def __call__(self, val):
#         return True
#
#
# class PedigreeSelectorFilter(object):
#
#     def __init__(self, pedigree_query):
#         self.pedigree_query = pedigree_query
#         self.id = pedigree_query['id']
#         self.checked_values = set()
#         for value in pedigree_query['checkedValues']:
#             self.checked_values.add(value)
#
#     def __call__(self, variant):
#         return variant.atts[self.id] in self.checked_values
#
#     @staticmethod
#     def build(**kwargs):
#         if 'pedigreeSelector' not in kwargs:
#             return AllFilter()
#         pedigree_query = kwargs['pedigreeSelector']
#         assert 'id' in pedigree_query
#         assert 'checkedValues' in pedigree_query
#         return PedigreeSelectorFilter(pedigree_query)


class Dataset(QueryBase):

    def __init__(self, dataset_descriptor):
        self.descriptor = dataset_descriptor
        self.pheno_db = None
        self.families = None

        self._studies = None
        self._denovo_studies = None
        self._transmitted_studies = None

        self.load_pheno_db()

    @property
    def studies(self):
        if self._studies is None:
            study_names = [
                st.strip() for st in self.descriptor['studies'].split(',')
            ]
            studies = [vDB.get_studies(st) for st in study_names]
            self._studies = [
                st for st in itertools.chain.from_iterable(studies)
            ]
        return self._studies

    @property
    def denovo_studies(self):
        if self._denovo_studies is None:
            self._denovo_studies = [
                st for st in self.studies
                if st.has_denovo
            ]
        return self._denovo_studies

    @property
    def transmitted_studies(self):
        if self._transmitted_studies is None:
            self._transmitted_studies = [
                st for st in self.studies
                if st.has_transmitted
            ]
        return self._transmitted_studies

    def load(self):
        self.load_families()
        self.load_pedigree_selectors()

    def load_pheno_db(self):
        pheno_db = None
        if 'phenoDB' in self.descriptor:
            pheno_id = self.descriptor['phenoDB']
            if pheno.has_pheno_db(pheno_id):
                pheno_db = pheno.get_pheno_db(pheno_id)
        self.pheno_db = pheno_db

    def load_families(self):
        families = {}
        for st in self.denovo_studies:
            families.update(st.families)
        for st in self.transmitted_studies:
            families.update(st.families)
        self.families = families
        self.persons = {}
        for fam in self.families.values():
            for p in fam.memberInOrder:
                self.persons[p.personId] = p

    def load_pedigree_selectors(self):
        pedigree_selectors = self.descriptor['pedigreeSelectors']
        if pedigree_selectors is None:
            return None
        for pedigree_selector in pedigree_selectors:
            source = pedigree_selector['source']
            if source == 'legacy':
                assert pedigree_selector['id'] == 'phenotype'
            else:
                parts = [p.strip() for p in source.split('.')]
                assert 3 == len(parts)
                pheno_db, instrument, measure = parts
                assert pheno_db == 'phenoDB'
                assert self.pheno_db is not None
                measure_id = '{}.{}'.format(instrument, measure)
                assert self.pheno_db.has_measure(measure_id)
                self.supplement_pedigree_selector(
                    pedigree_selector, measure_id)

    def supplement_pedigree_selector(self, pedigree_selector, measure_id):
        assert self.families
        pedigree_id = pedigree_selector['id']
        default_value = pedigree_selector['default']['id']

        measure_values = self.pheno_db.get_measure_values(
            measure_id,
            person_ids=self.persons.keys())
        for p in self.persons.values():
            value = measure_values.get(p.personId, default_value)
            p.atts[pedigree_id] = value

    def get_pedigree_selector(self, **kwargs):
        pedigrees = self.descriptor['pedigreeSelectors']
        pedigree = pedigrees[0]
        if 'pedigreeSelector' in kwargs:
            assert 'id' in kwargs['pedigreeSelector']
            pedigreeSelectorId = kwargs['pedigreeSelector']['id']
            pedigree = self.idlist_get(pedigrees, pedigreeSelectorId)
        assert pedigree is not None
        return pedigree

    def get_denovo_filters(self, safe=True, **kwargs):
        return {
            'effectTypes': self.get_effect_types(
                safe=safe,
                dataset_descriptor=self.descriptor,
                **kwargs)
        }

    def get_denovo_variants(self, safe=True, **kwargs):
        denovo_filters = self.get_denovo_filters(safe, **kwargs)

        seen_vs = set()
        for st in self.denovo_studies:
            for v in st.get_denovo_variants(**denovo_filters):
                v_key = v.familyId + v.location + v.variant
                if v_key in seen_vs:
                    continue
                yield v
                seen_vs.add(v_key)

    def get_variants_preview(self, safe=True, **kwargs):
        denovo = self.get_denovo_variants(safe, **kwargs)
        legend = self.get_pedigree_selector(**kwargs)

        variants = itertools.chain.from_iterable([denovo])

        def augment_vars(v):
            chProf = "".join((p.role + p.gender for p in v.memberInOrder[2:]))

            v.atts["_par_races_"] = 'NA:NA'
            v.atts["_ch_prof_"] = chProf
            v.atts["_prb_viq_"] = 'NA'
            v.atts["_prb_nviq_"] = 'NA'
            v.atts["_pedigree_"] = v.pedigree_v3(legend)
            v.atts["_phenotype_"] = v.study.get_attr('study.phenotype')
            v._phenotype_ = v.study.get_attr('study.phenotype')
            return v

        return generate_response(
            itertools.imap(augment_vars, variants),
            [
                'effectType',
                'effectDetails',
                'all.altFreq',
                'all.nAltAlls',
                'SSCfreq',
                'EVSfreq',
                'E65freq',
                'all.nParCalled',
                '_par_races_',
                '_ch_prof_',
                '_prb_viq_',
                '_prb_nviq_',
                'valstatus',
                "_pedigree_",
                "phenoInChS"
            ])


class DatasetsFactory(dict):

    def __init__(self, datasets_config):
        self.datasets_config = datasets_config

    def get_dataset(self, dataset_id):
        if dataset_id in self:
            return self[dataset_id]
        dataset_descriptor = self.datasets_config.get_dataset(dataset_id)
        dataset = Dataset(dataset_descriptor)
        dataset.load()

        self[dataset_id] = dataset
        return dataset
