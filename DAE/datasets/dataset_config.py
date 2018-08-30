from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig


class DatasetConfig(ConfigurableEntityConfig):

    def __init__(self, *args, **kwargs):
        super(DatasetConfig, self).__init__(*args, **kwargs)
        assert self.dataset_id
        assert self.dataset_name
        assert self.id
        assert self.name
        assert self.description
        assert self.study_group
        assert self.data_dir
        assert 'phenotypeBrowser' in self
        assert 'phenotypeGenotypeTool' in self
        assert self.authorizedGroups
        assert 'studyTypes' in self
        assert 'phenoDB' in self
        assert 'enrichmentTool' in self
        enrichmentTool = dict(self)['enrichmentTool']
        if enrichmentTool:
            assert enrichmentTool['studyTypes']
            assert enrichmentTool['selector']
        assert 'genotypeBrowser' in self
        genotypeBrowser = dict(self)['genotypeBrowser']
        if genotypeBrowser:
            assert 'genesBlockShowAll' in genotypeBrowser
            assert 'hasFamilyFilters' in genotypeBrowser
            assert 'hasStudyFilters' in genotypeBrowser
            assert 'phenoFilters' in genotypeBrowser
            assert 'hasPresentInChild' in genotypeBrowser
            assert 'hasPresentInParent' in genotypeBrowser
            assert 'hasStudyTypes' in genotypeBrowser
            assert 'hasPedigreeSelector' in genotypeBrowser
            assert 'hasComplex' in genotypeBrowser
            assert 'hasCNV' in genotypeBrowser
            assert 'hasDenovo' in genotypeBrowser
            assert 'hasTransmitted' in genotypeBrowser
            assert genotypeBrowser['mainForm']
            assert 'phenoColumns' in genotypeBrowser
            assert 'familyStudyFilters' in genotypeBrowser
            assert 'phenoFilters' in genotypeBrowser
            assert genotypeBrowser['previewColumns']
            assert genotypeBrowser['downloadColumns']
            assert 'genotypeColumns' in genotypeBrowser
        assert 'pedigreeSelectors' in self
        pedigreeSelectors = dict(self)['pedigreeSelectors']
        for pedigree in pedigreeSelectors:
            assert pedigree['name']
            assert pedigree['id']
            assert pedigree['domain']
            assert pedigree['default']
            assert pedigree['source']
            assert pedigree['values']

        print("study_group", self.study_group)

    @staticmethod
    def _split_section(section):
        index = section.find('.')
        if index == -1:
            return (section, None)
        section_type = section[:index]
        section_name = section[index + 1:]
        return (section_type, section_name)

    @staticmethod
    def _new_keys_names():
        return {
            'phenotypebrowser': 'phenotypeBrowser',
            'phenogenotool': 'phenotypeGenotypeTool',
            'authorizedgroups': 'authorizedGroups',
            'studytypes': 'studyTypes',
            'phenodb': 'phenoDB',
            'enrichmenttool': 'enrichmentTool',
            'enrichmenttool.selector': 'enrichmentTool.selector',
            'enrichmenttool.studytypes': 'enrichmentTool.studyTypes',
            'genotypebrowser': 'genotypeBrowser',
            'genotypebrowser.genesblockshowall':
                'genotypeBrowser.genesBlockShowAll',
            'genotypebrowser.hasfamilyfilters':
                'genotypeBrowser.hasFamilyFilters',
            'genotypebrowser.hasstudyfilters':
                'genotypeBrowser.hasStudyFilters',
            'genotypebrowser.phenofilters': 'genotypeBrowser.phenoFilters',
            'genotypebrowser.haspresentinchild':
                'genotypeBrowser.hasPresentInChild',
            'genotypebrowser.haspresentinparent':
                'genotypeBrowser.hasPresentInParent',
            'genotypebrowser.hasstudytypes': 'genotypeBrowser.hasStudyTypes',
            'genotypebrowser.haspedigreeselector':
                'genotypeBrowser.hasPedigreeSelector',
            'genotypebrowser.hascomplex': 'genotypeBrowser.hasComplex',
            'genotypebrowser.hascnv': 'genotypeBrowser.hasCNV',
            'genotypebrowser.hasdenovo': 'genotypeBrowser.hasDenovo',
            'genotypebrowser.hastransmitted': 'genotypeBrowser.hasTransmitted',
            'genotypebrowser.mainform': 'genotypeBrowser.mainForm',
            'genotypebrowser.phenocolumns': 'genotypeBrowser.phenoColumns',
            'genotypebrowser.familyfilters':
                'genotypeBrowser.familyStudyFilters',
            'genotypebrowser.phenofilters.filters':
                'genotypeBrowser.phenoFilters.filters',
            'genotypebrowser.genotype.basecolumns':
                'genotypeBrowser.genotype.baseColumns',
            'genotypebrowser.genotype.columns':
                'genotypeBrowser.genotype.columns',
            'genotypebrowser.basepreviewcolumns':
                'genotypeBrowser.basePreviewColumns',
            'genotypebrowser.previewcolumns': 'genotypeBrowser.previewColumns',
            'genotypebrowser.basedownloadcolumns':
                'genotypeBrowser.baseDownloadColumns',
            'genotypebrowser.downloadcolumns':
                'genotypeBrowser.downloadColumns'
        }

    @staticmethod
    def _split_str_lists_keys():
        return [
            'authorizedGroups', 'phenoDB',
            'genotypeBrowser.phenoFilters',
            'genotypeBrowser.baseColumns',
            'genotypeBrowser.basePreviewColumns',
            'genotypeBrowser.baseDownloadColumns',
            'genotypeBrowser.previewColumns', 'genotypeBrowser.downloadColumns'
            'genotypeBrowser.phenoColumns',
            'genotypeBrowser.familyStudyFilters',
            'genotypeBrowser.phenoFilters.filters',
            'genotypeBrowser.genotype.columns'
        ]

    @staticmethod
    def _cast_to_bool_keys():
        return [
            'phenotypeBrowser', 'phenotypeGenotypeTool', 'enrichmentTool',
            'genotypeBrowser', 'genotypeBrowser.genesBlockShowAll',
            'genotypeBrowser.hasPresentInParent', 'genotypeBrowser.hasComplex',
            'genotypeBrowser.hasStudyTypes', 'genotypeBrowser.hasTransmitted',
            'genotypeBrowser.hasPresentInChild', 'genotypeBrowser.hasDenovo',
            'genotypeBrowser.hasPedigreeSelector', 'genotypeBrowser.hasCNV',
            'genotypeBrowser.hasFamilyFilters',
            'genotypeBrowser.hasStudyFilters'
        ]

    @staticmethod
    def _concat_two_options(dataset_config):
        concat_options = {
            'genotypeBrowser.baseColumns':
                'genotypeBrowser.columns',
            'genotypeBrowser.basePreviewColumns':
                'genotypeBrowser.previewColumns',
            'genotypeBrowser.baseDownloadColumns':
                'genotypeBrowser.downloadColumns'
        }

        for first, second in concat_options.items():
            dataset_config[second] =\
                ','.join(filter(None, [dataset_config.pop(first, None),
                                       dataset_config.pop(second, None)]))

        return dataset_config

    @staticmethod
    def _copy_elements(dataset_config):
        elements_to_copy = {
            'dataset_id': 'id', 'dataset_name': 'name'
        }

        for old, new in elements_to_copy.items():
            dataset_config[new] = dataset_config[old]

        return dataset_config

    @staticmethod
    def _combine_dict_options(dataset_config):
        dict_options_keys = [
            'enrichmentTool', 'genotypeBrowser']

        for key in dict_options_keys:
            if dataset_config.get(key, True):
                dict_options = {}
                for k in dataset_config.keys():
                    if k.startswith(key + '.'):
                        dict_options[k.replace(key + '.', '')] =\
                            dataset_config.pop(k)
                dataset_config[key] = dict_options

        return dataset_config

    @staticmethod
    def _get_values(options):
        return {option['id']: option for option in options}

    @staticmethod
    def _pedigree_selectors_split_dict(dict_to_split):
        options = dict_to_split.split(':')
        return {'id': options[0], 'name': options[1], 'color': options[2]}

    @classmethod
    def _split_dict_lists(cls, dict_to_split):
        options = [cls._pedigree_selectors_split_dict(el.strip())
                   for el in dict_to_split.split(',')]
        return options

    @classmethod
    def _get_pedigree(cls, pedigree_type, pedigree_options, dataset_config):
        pedigree = {}

        pedigree['name'] = dataset_config.pop(pedigree_type + '.name', None)
        pedigree['source'] = dataset_config.pop(pedigree_type + '.source',
                                                None)
        pedigree['id'] = dataset_config.pop(pedigree_type + '.id',
                                            pedigree['name'])
        pedigree['default'] =\
            cls._pedigree_selectors_split_dict(
                dataset_config.pop(pedigree_type + '.default'))
        pedigree['domain'] =\
            cls._split_dict_lists(
                dataset_config.pop(pedigree_type + '.domain'))
        pedigree['values'] =\
            cls._get_values(pedigree['domain'])

        return pedigree

    @classmethod
    def _get_pedigree_selectors(cls, dataset_config):
        pedigree = {}
        for key, value in dataset_config.items():
            option_type, option_fullname = cls._split_section(key)
            if option_type != 'pedigree':
                continue

            pedigree_type, pedigree_option =\
                cls._split_section(option_fullname)
            if 'pedigree.' + pedigree_type not in pedigree:
                pedigree['pedigree.' + pedigree_type] = [pedigree_option]
            else:
                pedigree['pedigree.' + pedigree_type].append(pedigree_option)

        pedigrees = []
        for pedigree_type, pedigree_options in pedigree.items():
            if 'domain' in pedigree_options:
                pedigrees.append(cls._get_pedigree(
                    pedigree_type, pedigree_options, dataset_config))

        return pedigrees

    @staticmethod
    def _get_genotype_browser_pheno_filter(dataset_config, f):
        prefix = 'genotypebrowser.phenofilters.{}'.format(f)
        name = dataset_config.pop('{}.{}'.format(prefix, 'name'), None)
        measure_type = dataset_config.pop(
            '{}.{}'.format(prefix, 'type'), None)
        mf = dataset_config.pop('{}.{}'.format(prefix, 'filter'), None)
        mf = mf.split(':')
        if 'single' == mf[0]:
            filter_type, role, measure = mf
            measure_filter = {
                'filterType': filter_type,
                'role': role,
                'measure': measure
            }
        elif 'multi' == mf[0]:
            filter_type, role = mf
            measure_filter = {
                'filterType': filter_type,
                'role': role
            }
        return {
            'name': name,
            'measureType': measure_type,
            'measureFilter': measure_filter
        }

    @classmethod
    def _get_genotype_browser_pheno_filters(cls, dataset_config):
        result = []
        filters = dataset_config.pop(
            'genotypeBrowser.phenoFilters.filters', None)

        if not filters:
            return None

        for f in filters:
            pheno_filter =\
                cls._get_genotype_browser_pheno_filter(dataset_config, f)
            result.append(pheno_filter)

        return result

    @staticmethod
    def _get_genotype_browser_genotype_column(dataset_config, col_id):
        prefix = 'genotypebrowser.genotype.{}'.format(col_id)
        name = dataset_config.pop('{}.{}'.format(prefix, 'name'), None)
        source = dataset_config.pop('{}.{}'.format(prefix, 'source'), None)
        slots = dataset_config.pop('{}.{}'.format(prefix, 'slots'), None)

        if slots:
            slots = slots.split(',')

        column = {}
        column['id'] = col_id
        column['name'] = name
        column['source'] = source

        column_slots = []
        for slot in slots or []:
            slot_arr = [el.strip() for el in slot.split(':')]
            if len(slot_arr) == 1:
                source = slot_arr[0]
                label = slot_arr[0]
                label_format = "%s"
            elif len(slot_arr) == 2:
                source, label = slot_arr
                label_format = "%s"
            elif len(slot_arr) == 3:
                source, label, label_format = slot_arr
            column_slots.append(
                {
                    'source': source,
                    'name': label,
                    'id': source,
                    'format': label_format
                })
        column['slots'] = column_slots
        return column

    @classmethod
    def _get_genotype_browser_genotype_columns(cls, dataset_config):
        result = []
        columns = dataset_config.pop('genotypeBrowser.genotype.columns', None)
        if not columns:
            return None

        for col in columns:
            column =\
                cls._get_genotype_browser_genotype_column(dataset_config, col)
            result.append(column)
        return result

    @classmethod
    def from_config(cls, config_section, section=None):
        dataset_config = config_section

        dataset_config =\
            cls._change_keys_names(cls._new_keys_names(), dataset_config)
        dataset_config = cls._concat_two_options(dataset_config)
        dataset_config =\
            cls._split_str_lists(cls._split_str_lists_keys(), dataset_config)
        dataset_config =\
            cls._cast_to_bool(cls._cast_to_bool_keys(), dataset_config)
        dataset_config = cls._copy_elements(dataset_config)
        dataset_config['pedigreeSelectors'] =\
            cls._get_pedigree_selectors(dataset_config)
        dataset_config['genotypeBrowser.phenoFilters'] =\
            cls._get_genotype_browser_pheno_filters(dataset_config)
        dataset_config['genotypeBrowser.genotypeColumns'] =\
            cls._get_genotype_browser_genotype_columns(dataset_config)
        dataset_config = cls._combine_dict_options(dataset_config)

        dataset_config['authorizedGroups'] = dataset_config.get(
            'authorizedGroups', [dataset_config['dataset_id']])

        return DatasetConfig(dataset_config)

    @staticmethod
    def get_default_values():
        return {
            'studyTypes': None,
            'phenoDB': None,
            'genotypeBrowser.genesBlockShowAll': 'yes',
            'genotypeBrowser.hasFamilyFilters': 'yes',
            'genotypeBrowser.hasStudyFilters': 'yes',
            'genotypeBrowser.phenoFilters': '',
            'genotypeBrowser.hasPresentInChild': 'yes',
            'genotypeBrowser.hasPresentInParent': 'yes',
            'genotypeBrowser.hasStudyTypes': 'no',
            'genotypeBrowser.hasPedigreeSelector': 'no',
            'genotypeBrowser.hasComplex': 'no',
            'genotypeBrowser.hasCNV': 'no',
            'genotypeBrowser.hasDenovo': 'no',
            'genotypeBrowser.hasTransmitted': 'no',
            'genotypeBrowser.mainForm': 'default',
            'genotypeBrowser.phenoColumns': '',
            'genotypeBrowser.familyFilters': None,
            'pedigree.phenotype.source': 'legacy',
            'pedigree.phenotype.default': 'unknown:unknown:#aaaaaa',
            'genotypeBrowser.baseColumns':
                'family,phenotype,variant,best,fromparent,inchild,genotype,'
                'effect,count,geneeffect,effectdetails,weights,freq',
            'genotypeBrowser.basePreviewColumns':
                'family,variant,genotype,effect,weights,freq',
            'genotypeBrowser.baseDownloadColumns':
                'family,phenotype,variant,best,fromparent,inchild,effect,'
                'count,geneeffect,effectdetails,weights,freq',
            'phenoFilters': ''
        }

    @staticmethod
    def _get_dataset_description_keys():
        return [
            'id', 'name', 'description', 'studies', 'data_dir',
            'phenotypeBrowser', 'phenotypeGenotypeTool', 'authorizedGroups',
            'studyTypes', 'phenoDB', 'enrichmentTool', 'genotypeBrowser',
            'pedigreeSelectors'
        ]

    def get_dataset_description(self):
        keys = DatasetConfig._get_dataset_description_keys()
        dataset_config = self.to_dict()

        return {key: dataset_config[key] for key in keys}
