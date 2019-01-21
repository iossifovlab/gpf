
class StudyBase(object):

    def __init__(self, name, study_config):
        self.name = name
        self.study_config = study_config

        genotype_browser = study_config.genotypeBrowser

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

        if study_config.pedigreeSelectors:
            pedigree_selectors = study_config.pedigreeSelectors

        self.study_config = study_config

        self.name = name
        self.id = study_config.id
        self.phenotypes = self.study_config.phenotypes
        self.has_denovo = self.study_config.has_denovo
        self.has_transmitted = self.study_config.has_transmitted
        self.has_complex = self.study_config.has_complex
        self.has_cnv = self.study_config.has_cnv
        self.study_type = self.study_config.study_type
        self.study_types = [self.study_type]

        self.year = self.study_config.year
        self.years = [self.year] if self.year is not None else []
        self.pub_med = self.study_config.pub_med
        self.pub_meds = [self.pub_med] if self.pub_med is not None else []

        self.preview_columns = preview_columns
        self.download_columns = download_columns
        self.pedigree_columns = pedigree_columns
        self.pheno_columns = pheno_columns

        self.pedigree_selectors = pedigree_selectors

        if len(self.study_config.pedigreeSelectors) != 0:
            self.legend = {ps['id']: ps['domain'] + [ps['default']]
                           for ps in self.study_config.pedigreeSelectors}
        else:
            self.legend = {}

    # def _transform_variants_kwargs(self, **kwargs):
    #     if 'pedigreeSelector' in kwargs:
    #         pedigree_selector_id = kwargs['pedigreeSelector']['id']
    #         pedigree_selectors = list(filter(
    #             lambda ps: ps['id'] == pedigree_selector_id,
    #             self.pedigree_selectors))
    #         if pedigree_selectors:
    #             pedigree_selector = pedigree_selectors[0]
    #             kwargs['pedigreeSelector']['source'] =\
    #                 pedigree_selector['source']

    #     return kwargs

    def query_variants(self, **kwargs):
        # kwargs = self._transform_variants_kwargs(**kwargs)

        # study_types_filter = kwargs.get('studyTypes', None)
        # if study_types_filter:
        #     assert isinstance(study_types_filter, list)
        #     study_types_filter = [s.lower() for s in study_types_filter]
        #     if self._study_type_lowercase not in study_types_filter:
        #         return []

        kwargs = self.add_people_with_phenotype(kwargs)
        if 'person_ids' in kwargs and len(kwargs['person_ids']) == 0:
            return []

        return self.backend.query_variants(**kwargs)

    def add_people_with_phenotype(self, kwargs):
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

    def get_phenotype_values(self, pheno_column='phenotype'):
        return set(self.backend.ped_df[pheno_column])

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

    @staticmethod
    def _get_description_keys():
        return [
            'id', 'name', 'description', 'data_dir', 'phenotypeBrowser',
            'phenotypeGenotypeTool', 'authorizedGroups', 'phenoDB',
            'enrichmentTool', 'genotypeBrowser', 'pedigreeSelectors',
            'studyTypes', 'studies'
        ]

    @property
    def order(self):
        return 0

    @property
    def families(self):
        return self.backend.families

    @property
    def description(self):
        return self.study_config.description

    # FIXME: fill these with real data


class Study(StudyBase):

    def __init__(self, name, backend, study_config):
        super(Study, self).__init__(name, study_config)

        self.backend = backend
        self._study_type_lowercase = self.study_type.lower()

