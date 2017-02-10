'''
Created on Feb 9, 2017

@author: lubo
'''
from DAE import pheno
from datasets.query import QueryDataset, PedigreeLegend
import itertools
from query_variants import generate_response
from common.query_base import QueryBase


class Dataset(QueryBase):

    def __init__(self, dataset_descriptor):
        self.descriptor = dataset_descriptor
        self.query = QueryDataset()
        self.denovo_studies = None
        self.transmitted_studies = None
        self.pheno_db = None
        self.families = None
        self.denovo_studies = \
            self.query.get_denovo_studies(self.descriptor)
        self.transmitted_studies = \
            self.query.get_transmitted_studies(self.descriptor)
        self.pheno_db = self.load_pheno_db()

    def load(self):
        self.families = self.load_families()
        self.load_pedigree_selectors()

    def load_pheno_db(self):
        pheno_db = None
        if 'phenoDB' in self.descriptor:
            pheno_id = self.descriptor['phenoDB']
            if pheno.has_pheno_db(pheno_id):
                pheno_db = pheno.get_pheno_db(pheno_id)
        return pheno_db

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
            pedigree = self.idlist_get(pedigrees, kwargs['pedigreeSelector'])
        assert pedigree is not None
        return pedigree

    def get_legend(self, **kwargs):
        pedigree = self.get_pedigree_selector(**kwargs)
        return PedigreeLegend(pedigree)

    def get_denovo_variants(self, safe=True, **kwargs):
        denovo_filters = self.query.get_denovo_filters(
            self.descriptor, safe, **kwargs)

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
        legend = self.get_legend(**kwargs)

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
