'''
Created on Aug 9, 2016

@author: lubo
'''
from api.query.wdae_query_variants import prepare_query_dict,\
    wdae_handle_gene_sets
from helpers.logger import LOGGER
from pheno_families.pheno_filter import FamilyFilter
from pheno_families.views import PhenoFamilyBase

import preloaded
from pheno.measures import NormalizedMeasure
from api.default_ssc_study import get_ssc_all


class Request(PhenoFamilyBase):

    DEFAULT_EFFECT_TYPE_GROUPS = [
        'LGDs',
        'missense',
        'synonymous',
        'CNV+,CNV-',
    ]

    def _prepare_studies(self):
        self.data.update(get_ssc_all())
        if 'presentInParent' not in self.data or \
                self.data['presentInParent'] is None or \
                self.data['presentInParent'] == 'neither':

            del self.data['transmittedStudies']

    def _prepare_families_data(self):
        self.siblings = self.prepare_siblins(self.data)
        self.probands = self.prepare_probands(self.data)
        self.families = [
            FamilyFilter.strip_proband_id(p) for p in self.probands]
        if self.families:
            self.data['familyIds'] = ",".join(self.families)

    def _prepare_effect_groups(self):
        if 'effectTypeGroups' in self.data:
            self.effect_type_groups = self.data['effectTypeGroups'].split(',')
            del self.data['effectTypeGroups']
        else:
            self.effect_type_groups = self.DEFAULT_EFFECT_TYPE_GROUPS

    def _prepare_normalize_by(self):
        norm_by = set()
        if 'normalizedBy' in self.data:
            norm_by = set(self.data['normalizedBy'].split(','))

        res = []
        if 'normByAge' in norm_by:
            res.append('age')
        if 'normByVIQ' in norm_by:
            res.append('verbal_iq')
        if 'normByNVIQ' in norm_by:
            res.append('non_verbal_iq')
        return res

    def _prepare_pheno_measure(self):
        if 'phenoMeasure' not in self.data:
            LOGGER.error("phenoMeasure not found")
            raise ValueError("phenoMeasure parameter not found in request")

        self.measure_name = self.data['phenoMeasure']
        measures = preloaded.register.get_register().get('pheno_measures')
        if not measures.has_measure(self.measure_name):
            return ValueError("pheno measure {} not found"
                              .format(self.measure_name))

        self.by = self._prepare_normalize_by()
        self.nm = NormalizedMeasure(self.measure_name)
        self.nm.normalize(by=self.by)

    def __init__(self, data):
        PhenoFamilyBase.__init__(self)

        self.data = prepare_query_dict(data)
        wdae_handle_gene_sets(self.data)

        self._prepare_studies()
        self._prepare_families_data()
        self._prepare_effect_groups()

        self._prepare_pheno_measure()
