from builtins import str


class StudyWdaeMixin(object):

    @staticmethod
    def _split_section(section):
        index = section.find('.')
        if index == -1:
            return (section, None)
        section_type = section[:index]
        section_name = section[index + 1:]
        return (section_type, section_name)

    @staticmethod
    def _combine_dict_options(
        dataset_config, dict_options_keys=[
            'enrichmentTool', 'genotypeBrowser']):

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
                if dict_options:
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
    def _get_pedigree(cls, pedigree_type, pedigree_options, study_config):
        pedigree = {}

        pedigree['name'] = study_config.pop(pedigree_type + '.name', None)
        pedigree['source'] = study_config.get(pedigree_type + '.source', None)
        _, pedigree['id'] = cls._split_section(pedigree_type)
        pedigree['default'] =\
            cls._pedigree_selectors_split_dict(
                study_config.pop(pedigree_type + '.default'))
        pedigree['domain'] =\
            cls._split_dict_lists(
                study_config.pop(pedigree_type + '.domain'))
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
        name_key = '{}.{}'.format(prefix, 'name')
        slots_key = '{}.{}'.format(prefix, 'slots')
        name = dataset_config.pop(name_key)
        slots = dataset_config.pop(slots_key, None)
        if slots is None:
            slots = []
        else:
            slots = list(map(str.strip, slots.split(',')))

        column = {}
        column['id'] = col_id
        column['name'] = name

        column_slots = []
        for slot in slots:
            role, source, label = slot.split(':')
            column_slots.append(
                {
                    'role': role,
                    'measure': source,
                    'source': '{}.{}'.format(role, source),
                    'name': label,
                    'id': '{}.{}'.format(role, source),
                })
        column['slots'] = column_slots
        return column

    @classmethod
    def _get_genotype_browser_pheno_columns(cls, dataset_config):
        result = []
        columns = dataset_config.pop('genotypeBrowser.pheno.columns', None)
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

    @staticmethod
    def _get_genotype_browser_column_slots(genotype_columns, columns):
        column_slots = []
        for column in columns:
            genotype_column = list(filter(
                lambda genotype_column: genotype_column['id'] == column,
                genotype_columns
            ))

            if len(genotype_column) == 0:
                continue
            gc = genotype_column[0]

            if 'source' in gc and gc['source'] is not None:
                column_slots.append(gc['source'])

            for slot in gc['slots']:
                if slot['source'] is not None:
                    column_slots.append(slot['source'])

        return column_slots

    @classmethod
    def _fill_wdae_people_group_config(cls, config_section):
        people_group =\
            cls._get_pedigree_selectors(config_section, 'peopleGroup')
        if people_group:
            config_section['pedigreeSelectors'] = people_group
            config_section['peopleGroup'] = config_section['pedigreeSelectors']

    @classmethod
    def _fill_wdae_genotype_browser_config(cls, config_section):
        config_section['genotypeBrowser.pedigreeColumns'] =\
            cls._get_pedigree_selector_columns(
                config_section, 'genotypeBrowser', 'peopleGroup')
        config_section['genotypeBrowser.phenoFilters'] =\
            cls._get_genotype_browser_pheno_filters(config_section)
        config_section['genotypeBrowser.phenoColumns'] =\
            cls._get_genotype_browser_pheno_columns(config_section)
        config_section['genotypeBrowser.genotypeColumns'] =\
            cls._get_genotype_browser_genotype_columns(config_section) + \
            config_section['genotypeBrowser.pedigreeColumns'] + \
            config_section['genotypeBrowser.phenoColumns']
        config_section['genotypeBrowser.previewColumnsSlots'] =\
            cls._get_genotype_browser_column_slots(
                config_section.get('genotypeBrowser.genotypeColumns', []),
                config_section.get('genotypeBrowser.previewColumns', []))
        config_section['genotypeBrowser.downloadColumnsSlots'] =\
            cls._get_genotype_browser_column_slots(
                config_section.get('genotypeBrowser.genotypeColumns', []),
                config_section.get('genotypeBrowser.downloadColumns', []))

        config_section = cls._combine_dict_options(
            config_section,
            dict_options_keys=['genotypeBrowser'])

        genotype_browser = config_section['genotypeBrowser']
        if not genotype_browser:
            config_section['genotypeBrowser'] = False
            return

        for key, value in genotype_browser.items():
            if value:
                return
        config_section['genotypeBrowser'] = False

    @classmethod
    def _fill_wdae_enrichment_tool_config(cls, config_section):
        config_section = cls._combine_dict_options(
            config_section,
            dict_options_keys=['enrichmentTool'])

    @classmethod
    def _fill_wdae_config(cls, config_section):
        cls._fill_wdae_people_group_config(config_section)
        cls._fill_wdae_genotype_browser_config(config_section)
        cls._fill_wdae_enrichment_tool_config(config_section)
