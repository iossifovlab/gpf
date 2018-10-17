from __future__ import print_function
from __future__ import unicode_literals


class Dataset(object):

    def __init__(
            self, name, study_group, dataset_config):
        super(Dataset, self).__init__()
        genotypeBrowser = dataset_config.genotypeBrowser
        preview_columns = []
        download_columns = []
        if genotypeBrowser:
            preview_columns = genotypeBrowser['previewColumns']
            download_columns = genotypeBrowser['downloadColumns']

        self.name = name
        self.study_group = study_group

        self.dataset_config = dataset_config

        self.name = name
        self.preview_columns = preview_columns
        self.download_columns = download_columns

        if len(self.dataset_config.pedigreeSelectors) != 0:
            self.legend = self.dataset_config.pedigreeSelectors[0]['domain']
        else:
            self.legend = {}

    @property
    def id(self):
        return self.dataset_config.id

    @property
    def studies(self):
        return self.study_group.studies

    def get_variants(self, **kwargs):
        return self.study_group.get_variants(**kwargs)

    @property
    def study_names(self):
        return self.study_group.study_names

    # FIXME: fill these with real values
    def get_column_labels(self):
        return ['']

    def get_legend(self, *args, **kwargs):
        return self.legend

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
