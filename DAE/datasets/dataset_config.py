from configurable_entities.configurable_entity_config import \
    ConfigurableEntityConfig


class DatasetConfig(ConfigurableEntityConfig):

    NEW_KEYS_NAMES = {
        'phenoGenoTool': 'phenotypeGenotypeTool',
        'genotypeBrowser.familyFilters': 'genotypeBrowser.familyStudyFilters',
    }
    CONCAT_OPTIONS = {
        'genotypeBrowser.genotype.baseColumns':
            'genotypeBrowser.genotype.columns',
        'genotypeBrowser.basePreviewColumns': 'genotypeBrowser.previewColumns',
        'genotypeBrowser.baseDownloadColumns':
            'genotypeBrowser.downloadColumns'
    }
    SPLIT_STR_LISTS = (
        'authorizedGroups',
        'genotypeBrowser.phenoFilters',
        'genotypeBrowser.baseColumns',
        'genotypeBrowser.basePreviewColumns',
        'genotypeBrowser.baseDownloadColumns',
        'genotypeBrowser.previewColumns',
        'genotypeBrowser.downloadColumns',
        'genotypeBrowser.pheno.columns',
        'genotypeBrowser.familyStudyFilters',
        'genotypeBrowser.phenoFilters.filters',
        'genotypeBrowser.genotype.columns',
        'genotypeBrowser.peopleGroup.columns'
    )
    CAST_TO_BOOL = (
        'phenotypeBrowser', 'phenotypeGenotypeTool', 'enrichmentTool',
        'genotypeBrowser', 'genotypeBrowser.genesBlockShowAll',
        'genotypeBrowser.hasPresentInParent', 'genotypeBrowser.hasComplex',
        'genotypeBrowser.hasPresentInChild', 'genotypeBrowser.hasDenovo',
        'genotypeBrowser.hasPedigreeSelector', 'genotypeBrowser.hasCNV',
        'genotypeBrowser.hasFamilyFilters',
        'genotypeBrowser.hasStudyFilters',
        'genotypeBrowser.hasTransmitted',
    )
    ELEMENTS_TO_COPY = {
        'dataset_id': 'id', 'dataset_name': 'name'
    }

    def __init__(self, config, *args, **kwargs):
        super(DatasetConfig, self).__init__(config, *args, **kwargs)
        assert self.dataset_id
        assert self.dataset_name
        assert self.id
        assert self.name
        assert 'description' in self
        assert self.study_group
        assert self.data_dir
        assert 'phenotypeBrowser' in self
        assert 'phenotypeGenotypeTool' in self
        assert self.authorizedGroups
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
            assert 'hasPresentInChild' in genotypeBrowser
            assert 'hasPresentInParent' in genotypeBrowser
            assert 'hasPedigreeSelector' in genotypeBrowser
            assert genotypeBrowser['mainForm']
            assert 'phenoColumns' in genotypeBrowser
            assert 'familyStudyFilters' in genotypeBrowser
            assert 'phenoFilters' in genotypeBrowser
            assert 'pedigreeColumns' in genotypeBrowser
            assert genotypeBrowser['previewColumns']
            assert genotypeBrowser['downloadColumns']
            assert 'genotypeColumns' in genotypeBrowser
        assert 'pedigreeSelectors' in self
        pedigree_selectors = self['pedigreeSelectors']
        for pedigree in pedigree_selectors:
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
    def _combine_dict_options(dataset_config):
        dict_options_keys = [
            'enrichmentTool', 'genotypeBrowser']

        for key in dict_options_keys:
            if dataset_config.get(key, True):
                dict_options = {}
                keys_to_remove = []
                for k in dataset_config.keys():
                    if k.startswith(key + '.'):
                        keys_to_remove.append(k)
                        dict_options[k.replace(key + '.', '')] =\
                            dataset_config.get(k)
                for k in keys_to_remove:
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
        pedigree['source'] = dataset_config.get(pedigree_type + '.source',
                                                None)
        _, pedigree['id'] = cls._split_section(pedigree_type)
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
    def _get_pedigree_selectors(cls, dataset_config, pedigree_key):
        pedigree = {}
        for key, value in dataset_config.items():
            option_type, option_fullname = cls._split_section(key)
            if option_type != pedigree_key:
                continue

            pedigree_type, pedigree_option =\
                cls._split_section(option_fullname)
            if pedigree_key + '.' + pedigree_type not in pedigree:
                pedigree[pedigree_key + '.' + pedigree_type] =\
                    [pedigree_option]
            else:
                pedigree[pedigree_key + '.' + pedigree_type].append(
                    pedigree_option)

        pedigrees = []
        for pedigree_type, pedigree_options in pedigree.items():
            if 'domain' in pedigree_options:
                pedigrees.append(cls._get_pedigree(
                    pedigree_type, pedigree_options, dataset_config))

        return pedigrees

    @staticmethod
    def _get_pedigree_selector_column(
            pedigree_selector_column, dataset_config, parent_key,
            pedigree_key):

        pedigree = {}

        pedigree['id'] = pedigree_selector_column
        pedigree['name'] = dataset_config.pop(
            parent_key + '.' + pedigree_key + '.' + pedigree_selector_column +
            '.name', None)
        pedigree['role'] = dataset_config.pop(
            parent_key + '.' + pedigree_key + '.' + pedigree_selector_column +
            '.role', None)
        pedigree['source'] = dataset_config.get(
            pedigree_key + '.' + pedigree_selector_column + '.source', None)

        return pedigree

    @classmethod
    def _get_pedigree_selector_columns(
            cls, dataset_config, parent_key, pedigree_key):
        pedigree_selector_columns = dataset_config.pop(
            parent_key + '.' + pedigree_key + '.' + 'columns', None)
        if not pedigree_selector_columns:
            return []

        pedigrees = {}

        pedigrees['name'] = dataset_config.pop(
            parent_key + '.' + pedigree_key + '.' + 'columns.name')
        pedigrees['id'] = dataset_config.pop(
            parent_key + '.' + pedigree_key + '.' + 'columns.id',
            pedigrees['name'])
        pedigrees['slots'] = []

        for pedigree_selector_column in pedigree_selector_columns:
            pedigrees['slots'].append(cls._get_pedigree_selector_column(
                pedigree_selector_column, dataset_config, parent_key,
                pedigree_key))

        return [pedigrees]

    @staticmethod
    def _get_genotype_browser_pheno_filter(dataset_config, f):
        prefix = 'genotypeBrowser.phenoFilters.{}'.format(f)
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
    def _get_genotype_browser_pheno_column(dataset_config, col_id):
        prefix = 'genotypeBrowser.pheno.{}'.format(col_id)
        name = dataset_config.pop('{}.{}'.format(prefix, 'name'))
        slots = dataset_config.pop('{}.{}'.format(prefix, 'slots')).split(',')
        column = {}
        column['id'] = col_id
        column['name'] = name

        column_slots = []
        for slot in slots:
            role, source, label = slot.split(':')
            column_slots.append(
                {
                    'role': role,
                    'source': source,
                    'name': label,
                    'id': '{}.{}'.format(role, source),
                })
        column['slots'] = column_slots
        return column

    @classmethod
    def _get_genotype_browser_pheno_columns(cls, dataset_config):
        result = []
        columns = dataset_config.pop('genotypeBrowser.pheno.columns', None)
        print("pheno columns loaded", columns)
        if not columns:
            return []

        for col in columns:
            column = cls._get_genotype_browser_pheno_column(
                dataset_config, col)
            result.append(column)

        return result

    @staticmethod
    def _get_genotype_browser_genotype_column(dataset_config, col_id):
        prefix = 'genotypeBrowser.genotype.{}'.format(col_id)
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
            return []

        for col in columns:
            column =\
                cls._get_genotype_browser_genotype_column(dataset_config, col)
            result.append(column)
        return result

    @classmethod
    def from_config(cls, config_section, section=None):
        dataset_config = config_section

        dataset_config['pedigreeSelectors'] =\
            cls._get_pedigree_selectors(dataset_config, 'peopleGroup')
        dataset_config['genotypeBrowser.pedigreeColumns'] =\
            cls._get_pedigree_selector_columns(
                dataset_config, 'genotypeBrowser', 'peopleGroup')
        dataset_config['genotypeBrowser.phenoFilters'] =\
            cls._get_genotype_browser_pheno_filters(dataset_config)
        dataset_config['genotypeBrowser.phenoColumns'] =\
            cls._get_genotype_browser_pheno_columns(dataset_config)
        dataset_config['genotypeBrowser.genotypeColumns'] =\
            cls._get_genotype_browser_genotype_columns(dataset_config) + \
            dataset_config['genotypeBrowser.pedigreeColumns'] + \
            dataset_config['genotypeBrowser.phenoColumns']
        dataset_config = cls._combine_dict_options(dataset_config)

        dataset_config['authorizedGroups'] = dataset_config.get(
            'authorizedGroups', [dataset_config['dataset_id']])

        return DatasetConfig(dataset_config)

    @staticmethod
    def get_default_values():
        return {
            'phenoDB': None,
            'description': None,
            'genotypeBrowser.genesBlockShowAll': 'yes',
            'genotypeBrowser.hasFamilyFilters': 'yes',
            'genotypeBrowser.hasStudyFilters': 'yes',
            'genotypeBrowser.phenoFilters': '',
            'genotypeBrowser.hasPresentInChild': 'yes',
            'genotypeBrowser.hasPresentInParent': 'yes',
            'genotypeBrowser.hasPedigreeSelector': 'no',
            'genotypeBrowser.mainForm': 'default',
            'genotypeBrowser.pheno.columns': None,
            'genotypeBrowser.familyFilters': None,
            'genotypeBrowser.genotype.baseColumns':
                'family,phenotype,variant,best,fromparent,inchild,genotype,'
                'effect,count,geneeffect,effectdetails,weights,freq',
            'genotypeBrowser.basePreviewColumns':
                'family,variant,genotype,effect,weights,freq,studyName,'
                'location,pedigree,inChS,fromParentS,effects,'
                'requestedGeneEffects,genes,worstEffect',
            'genotypeBrowser.baseDownloadColumns':
                'family,phenotype,variant,best,fromparent,inchild,effect,'
                'count,geneeffect,effectdetails,weights,freq',
            'phenoFilters': '',
            'phenotypeBrowser': False,
            'phenotypeGenotypeTool': False,
        }
