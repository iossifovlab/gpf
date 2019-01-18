class Study(object):

    def __init__(self, name, backend, study_config):
        self.name = name
        self.backend = backend
        self.study_config = study_config
        self._study_type_lowercase = self.study_type.lower()

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

    def _transorm_variants_kwargs(self, **kwargs):
        if 'pedigreeSelector' in kwargs:
            pedigree_selector_id = kwargs['pedigreeSelector']['id']
            pedigree_selectors = list(filter(
                lambda ps: ps['id'] == pedigree_selector_id,
                self.pedigree_selectors))
            if pedigree_selectors:
                pedigree_selector = pedigree_selectors[0]
                kwargs['pedigreeSelector']['source'] =\
                    pedigree_selector['source']

        return kwargs

    def query_variants(self, **kwargs):
        kwargs = self._transorm_variants_kwargs(**kwargs)

        study_types_filter = kwargs.get('studyTypes', None)
        if study_types_filter:
            assert isinstance(study_types_filter, list)
            study_types_filter = [s.lower() for s in study_types_filter]
            if self._study_type_lowercase not in study_types_filter:
                return []

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

    @staticmethod
    def _get_description_keys():
        return [
            'id', 'name', 'description', 'data_dir', 'phenotypeBrowser',
            'phenotypeGenotypeTool', 'authorizedGroups', 'phenoDB',
            'enrichmentTool', 'genotypeBrowser', 'pedigreeSelectors',
            'studyTypes', 'studies'
        ]

    @property
    def families(self):
        return self.backend.families

    @property
    def description(self):
        return self.study_config.description

    @property
    def phenotypes(self):
        return self.study_config.phenotypes

    @property
    def has_denovo(self):
        return self.study_config.hasDenovo

    @property
    def has_transmitted(self):
        return self.study_config.hasTransmitted

    @property
    def has_complex(self):
        return self.study_config.hasComplex

    @property
    def has_CNV(self):
        return self.study_config.hasCNV

    @property
    def study_type(self):
        return self.study_config.studyType

    @property
    def study_types(self):
        return [self.study_config.studyType]

    # FIXME: fill these with real data

    @property
    def year(self):
        return None

    @property
    def years(self):
        return None

    @property
    def pub_med(self):
        return None

    @property
    def pub_meds(self):
        return None

