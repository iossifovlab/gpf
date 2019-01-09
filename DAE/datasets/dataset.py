from __future__ import print_function
from __future__ import unicode_literals


class Dataset(object):

    def __init__(
            self, name, study_group, dataset_config):
        super(Dataset, self).__init__()
        genotype_browser = dataset_config.genotypeBrowser

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

        if dataset_config.pedigreeSelectors:
            pedigree_selectors = dataset_config.pedigreeSelectors

        self.name = name
        self.study_group = study_group

        self.dataset_config = dataset_config

        self.name = name
        self.preview_columns = preview_columns
        self.download_columns = download_columns
        self.pedigree_columns = pedigree_columns
        self.pheno_columns = pheno_columns

        self.pedigree_selectors = pedigree_selectors

        if len(self.dataset_config.pedigreeSelectors) != 0:
            self.legend = {ps['id']: ps['domain'] + [ps['default']]
                           for ps in self.dataset_config.pedigreeSelectors}
        else:
            self.legend = {}

    @property
    def id(self):
        return self.dataset_config.id

    @property
    def studies(self):
        return self.study_group.studies

    def transorm_variants_kwargs(self, **kwargs):
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

    def get_variants(self, **kwargs):
        kwargs = self.transorm_variants_kwargs(**kwargs)

        return self.study_group.query_variants(**kwargs)

    @property
    def study_names(self):
        return self.study_group.study_names

    # FIXME: fill these with real values
    def get_column_labels(self):
        return ['']

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

    @property
    def order(self):
        return 0

    @staticmethod
    def _get_dataset_description_keys():
        return [
            'id', 'name', 'description', 'data_dir', 'phenotypeBrowser',
            'phenotypeGenotypeTool', 'authorizedGroups', 'phenoDB',
            'enrichmentTool', 'genotypeBrowser', 'pedigreeSelectors',
            'studyTypes', 'studies'
        ]

    def _get_study_group_config_options(self, dataset_config):
        dataset_config['studyTypes'] = self.study_group.study_types
        dataset_config['genotypeBrowser']['hasStudyTypes'] =\
            self.study_group.has_study_types
        dataset_config['genotypeBrowser']['hasComplex'] =\
            self.study_group.has_complex
        dataset_config['genotypeBrowser']['hasCNV'] =\
            self.study_group.has_CNV
        dataset_config['genotypeBrowser']['hasDenovo'] =\
            self.study_group.has_denovo
        dataset_config['genotypeBrowser']['hasTransmitted'] =\
            self.study_group.has_transmitted
        dataset_config['studies'] =\
            self.study_group.study_names

        return dataset_config

    def get_dataset_description(self):
        keys = Dataset._get_dataset_description_keys()
        dataset_config = self.dataset_config.to_dict()

        dataset_config = self._get_study_group_config_options(dataset_config)

        return {key: dataset_config[key] for key in keys}
