from __future__ import unicode_literals
from builtins import str

import itertools

from RegionOperations import Region
from variants.attributes import Role
from studies.helpers import expand_effect_types
from variants.attributes_query import role_query, variant_type_converter, \
    sex_converter, AndNode, NotNode, OrNode, ContainsNode


class StudyWrapper(object):

    def __init__(self, study, *args, **kwargs):
        super(StudyWrapper, self).__init__(*args, **kwargs)
        self.study = study
        self._init_wdae_config()

    def _init_wdae_config(self):
        genotype_browser = self.config.genotypeBrowser

        preview_columns = []
        download_columns = []
        pedigree_columns = {}
        pheno_columns = {}

        pedigree_selectors = []

        if genotype_browser:
            preview_columns = genotype_browser['previewColumns']
            download_columns = genotype_browser['downloadColumns']
            if genotype_browser['pedigreeColumns']:
                pedigree_columns =\
                    [s for pc in genotype_browser['pedigreeColumns']
                     for s in pc['slots']]
            if genotype_browser['phenoColumns']:
                pheno_columns = [s for pc in genotype_browser['phenoColumns']
                                 for s in pc['slots']]

        if 'pedigreeSelectors' in self.config:
            pedigree_selectors = self.config.pedigree_selectors

        self.preview_columns = preview_columns
        self.download_columns = download_columns
        self.pedigree_columns = pedigree_columns
        self.pheno_columns = pheno_columns

        self.pedigree_selectors = pedigree_selectors

        if len(self.pedigree_selectors) != 0:
            self.legend = {
                ps['id']: ps['domain'] + [ps['default']]
                for ps in self.pedigree_selectors
            }
        else:
            self.legend = {}

    def __getattr__(self, name):
        return getattr(self.study, name)

    FILTER_RENAMES_MAP = {
        'familyIds': 'family_ids',
        'gender': 'sexes',
        'geneSymbols': 'genes',
        'variantTypes': 'variant_type',
        'effectTypes': 'effect_types',
        'regionS': 'regions',
    }

    # Not implemented:
    # inChild
    # genomicScores
    # callSet
    # minParentsCalled
    # ultraRareOnly
    # TMM_ALL
    def query_variants(self, **kwargs):
        # print("kwargs in study group:", kwargs)
        kwargs = self._add_people_with_phenotype(kwargs)

        limit = None
        if 'limit' in kwargs:
            limit = kwargs['limit']

        if 'regions' in kwargs:
            kwargs['regions'] = list(map(Region.from_str, kwargs['regions']))

        if 'presentInChild' in kwargs:
            self._transform_present_in_child(kwargs)

        if 'presentInParent' in kwargs:
            self._transform_present_in_parent(kwargs)

        if 'minAltFrequencyPercent' in kwargs or \
                'maxAltFrequencyPercent' in kwargs:
            self._transform_min_max_alt_frequency(kwargs)

        for key in list(kwargs.keys()):
            if key in self.FILTER_RENAMES_MAP:
                kwargs[self.FILTER_RENAMES_MAP[key]] = kwargs[key]
                kwargs.pop(key)

        if 'sexes' in kwargs:
            sexes = kwargs['sexes']
            sexes = [ContainsNode(sex_converter(sex)) for sex in sexes]
            kwargs['sexes'] = OrNode(sexes)

        if 'variant_type' in kwargs:
            variant_types = kwargs['variant_type']
            variant_types = [ContainsNode(variant_type_converter(t))
                             for t in variant_types]
            kwargs['variant_type'] = OrNode(variant_types)

        if 'effect_types' in kwargs:
            kwargs['effect_types'] = expand_effect_types(
                kwargs['effect_types'])

        return itertools.islice(
            self.study.query_variants(**kwargs),
            limit)

    def _add_people_with_phenotype(self, kwargs):
        people_with_phenotype = set()
        if 'pedigreeSelector' in kwargs and\
                kwargs['pedigreeSelector'] is not None:
            pedigree_selector = kwargs.pop('pedigreeSelector')

            for family in self.families.values():
                family_members_with_phenotype = set(
                    [person.person_id for person in
                        family.get_people_with_phenotypes(
                            pedigree_selector['source'],
                            pedigree_selector['checkedValues'])])
                people_with_phenotype.update(family_members_with_phenotype)

            if 'person_ids' in kwargs:
                people_with_phenotype.intersection(kwargs['person_ids'])

            kwargs['person_ids'] = list(people_with_phenotype)

        return kwargs

    def _transform_min_max_alt_frequency(self, kwargs):
        min_value = None
        max_value = None

        if 'minAltFrequencyPercent' in kwargs:
            min_value = kwargs['minAltFrequencyPercent']
            kwargs.pop('minAltFrequencyPercent')

        if 'maxAltFrequencyPercent' in kwargs:
            max_value = kwargs['maxAltFrequencyPercent']
            kwargs.pop('maxAltFrequencyPercent')

        value_range = (min_value, max_value)

        if value_range == (None, None):
            return

        if value_range[0] is None:
            value_range = (float('-inf'), value_range[1])

        if value_range[1] is None:
            value_range = (value_range[0], float('inf'))

        print(value_range)

        value = 'af_allele_freq'
        if 'real_attr_filter' not in kwargs:
            kwargs['real_attr_filter'] = {}

        if value not in kwargs['real_attr_filter']:
            kwargs['real_attr_filter'][value] = []

        kwargs['real_attr_filter'][value].append(value_range)

    def _transform_present_in_child(self, kwargs):
        roles_query = []

        for filter_option in kwargs['presentInChild']:
            new_roles = None

            if filter_option == 'affected only':
                new_roles = AndNode([
                    ContainsNode(Role.prb),
                    NotNode(ContainsNode(Role.sib))
                ])

            if filter_option == 'unaffected only':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.prb)),
                    ContainsNode(Role.sib)
                ])

            if filter_option == 'affected and unaffected':
                new_roles = AndNode([
                    ContainsNode(Role.prb),
                    ContainsNode(Role.sib)
                ])

            if filter_option == 'neither':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.prb)),
                    NotNode(ContainsNode(Role.sib))
                ])

            if new_roles:
                roles_query.append(new_roles)

        kwargs.pop('presentInChild')

        if not roles_query:
            return

        roles_query = OrNode(roles_query)

        original_roles = kwargs.get('roles', None)
        if original_roles is not None:
            if isinstance(original_roles, str):
                original_roles = role_query.transform_query_string_to_tree(
                    original_roles)
            kwargs['roles'] = AndNode([original_roles, roles_query])
        else:
            kwargs['roles'] = roles_query

    def _transform_present_in_parent(self, kwargs):
        roles_query = []

        for filter_option in kwargs['presentInParent']:
            new_roles = None

            if filter_option == 'mother only':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.dad)),
                    ContainsNode(Role.mom)
                ])

            if filter_option == 'father only':
                new_roles = AndNode([
                    ContainsNode(Role.dad),
                    NotNode(ContainsNode(Role.mom))
                ])

            if filter_option == 'mother and father':
                new_roles = AndNode([
                    ContainsNode(Role.dad),
                    ContainsNode(Role.mom)
                ])

            if filter_option == 'neither':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.dad)),
                    NotNode(ContainsNode(Role.mom))
                ])

            if new_roles:
                roles_query.append(new_roles)

        kwargs.pop('presentInParent')

        if not roles_query:
            return

        roles_query = OrNode(roles_query)

        original_roles = kwargs.get('roles', None)
        if original_roles is not None:
            if isinstance(original_roles, str):
                original_roles = role_query.transform_query_string_to_tree(
                    original_roles)
            kwargs['roles'] = AndNode([original_roles, roles_query])
        else:
            kwargs['roles'] = roles_query

    def _get_legend_default_values(self):
        return [{
            'color': '#E0E0E0',
            'id': 'missing-person',
            'name': 'missing-person'
        }]

    def get_legend(self, *args, **kwargs):
        if 'pedigreeSelector' not in kwargs:
            legend = list(self.legend.values())[0] if self.legend else []
        else:
            legend = self.legend.get(kwargs['pedigreeSelector']['id'], [])

        return legend + self._get_legend_default_values()

    # FIXME:
    def _get_dataset_config_options(self, config):
        config['studyTypes'] = self.config.study_types
        config['genotypeBrowser']['hasStudyTypes'] =\
            self.config.has_study_types
        config['genotypeBrowser']['hasComplex'] =\
            self.config.has_complex
        config['genotypeBrowser']['hasCNV'] =\
            self.config.has_CNV
        config['genotypeBrowser']['hasDenovo'] =\
            self.config.has_denovo
        config['genotypeBrowser']['hasTransmitted'] =\
            self.config.has_transmitted
        config['studies'] =\
            self.config.names

        return config

    @staticmethod
    def _get_description_keys():
        return [
            'id', 'name', 'description', 'data_dir', 'phenotypeBrowser',
            'phenotypeGenotypeTool', 'authorizedGroups', 'phenoDB',
            'enrichmentTool', 'genotypeBrowser', 'pedigreeSelectors',
            'studyTypes', 'studies'
        ]

    # FIXME:
    def get_dataset_description(self):
        keys = self._get_dataset_description_keys()
        config = self.config.to_dict()

        config = self._get_dataset_config_options(config)

        return {key: config[key] for key in keys}
