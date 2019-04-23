from builtins import str

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig

from variants.attributes import Role


class GenotypeBrowserConfig(ConfigurableEntityConfig):

    CAST_TO_BOOL = (
        'genesBlockShowAll',
        'hasPresentInParent',
        'hasComplex',
        'hasPresentInChild',
        'hasPedigreeSelector',
        'hasCNV',
        'hasFamilyFilters',
        'hasStudyTypes',
        'hasStudyFilters',
        'hasPresentInRole',
        'hasGraphicalPreview',
    )

    SPLIT_STR_LISTS = [
        'phenoFilters',
        'baseColumns',
        'basePreviewColumns',
        'baseDownloadColumns',
        'previewColumns',
        'downloadColumns',
        'pheno.columns',
        'familyStudyFilters',
        'phenoFilters.filters',
        'genotype.columns',
        'peopleGroup.columns',
        'inRoles.columns'
    ]

    NEW_KEYS_NAMES = {
        'familyFilters': 'familyStudyFilters',
    }

    def __init__(self, config, *args, **kwargs):
        super(GenotypeBrowserConfig, self).__init__(config, *args, **kwargs)

    @staticmethod
    def _get_pheno_filter(dataset_config, f):
        prefix = 'phenoFilters.{}'.format(f)
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
    def _get_pheno_filters(cls, dataset_config):
        result = []
        filters = dataset_config.pop(
            'phenoFilters.filters', None)

        if not filters:
            return None

        for f in filters:
            pheno_filter =\
                cls._get_pheno_filter(dataset_config, f)
            result.append(pheno_filter)

        return result

    @staticmethod
    def _get_pheno_column(dataset_config, col_id):
        prefix = 'pheno.{}'.format(col_id)
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
    def _get_pheno_columns(cls, dataset_config):
        result = []
        columns = dataset_config.pop('pheno.columns', None)
        if not columns:
            return []

        for col in columns:
            column = cls._get_pheno_column(
                dataset_config, col)
            result.append(column)

        return result

    @staticmethod
    def _get_genotype_column(dataset_config, col_id):
        prefix = 'genotype.{}'.format(col_id)
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
    def _get_in_roles_columns(cls, dataset_config):
        result = []
        columns = dataset_config.pop('inRoles.columns', None)
        if not columns:
            return []

        for col in columns:
            column = cls._get_in_roles_column(
                dataset_config, col)
            result.append(column)

        return result

    @staticmethod
    def _get_in_roles_column(dataset_config, col_id):
        prefix = 'inRoles.{}'.format(col_id)
        roles = dataset_config.pop('{}.{}'.format(prefix, 'roles'))
        destination = dataset_config.pop(
            '{}.{}'.format(prefix, 'destination'), col_id)

        assert roles
        assert destination

        column = {
            'id': col_id,
            'roles': [role.strip() for role in roles.split(',')],
            'destination': destination
        }

        return column

    @classmethod
    def _get_genotype_columns(cls, dataset_config):
        result = []
        columns = dataset_config.pop('genotype.columns', None)
        if not columns:
            return []

        for col in columns:
            column =\
                cls._get_genotype_column(dataset_config, col)
            result.append(column)
        return result

    @staticmethod
    def _get_column_slots(genotype_columns, columns):
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

    @staticmethod
    def _get_column_labels(genotype_columns):
        column_labels = {}
        for gc in genotype_columns:
            if 'source' in gc and gc['source'] is not None:
                column_labels[gc['source']] = gc['name']

            for slot in gc['slots']:
                if slot['source'] is not None:
                    column_labels[slot['source']] = slot['name']

        return column_labels

    @staticmethod
    def _get_gene_weights_columns(genotype_columns):
        gene_weights_columns = list(filter(
            lambda gc: gc['id'] == 'weights', genotype_columns))

        if len(gene_weights_columns) == 0:
            return []

        gene_weights_slots = []
        for gwc in gene_weights_columns[0].get('slots', None):
            gene_weights_slots.append(gwc['id'])

        return gene_weights_slots

    @staticmethod
    def _split_section(section):
        index = section.find('.')
        if index == -1:
            return (section, None)
        section_type = section[:index]
        section_name = section[index + 1:]
        return (section_type, section_name)

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
    def _get_present_in_role(
            cls, present_in_role_type, present_in_role_options, study_config):
        present_in_role = {}

        present_in_role['name'] = \
            study_config.pop(present_in_role_type + '.name', None)
        present_in_role['roles'] = \
            [
                Role.from_name(el.strip()).display_name
                for el in study_config.pop(
                   present_in_role_type + '.roles').split(',')
            ]

        return present_in_role

    @classmethod
    def _get_selectors(cls, dataset_config, selector_key, selector_getter):
        selector = {}
        for key, value in dataset_config.items():
            option_type, option_fullname = cls._split_section(key)
            if option_type != selector_key:
                continue

            selector_type, selector_option =\
                cls._split_section(option_fullname)
            if selector_key + '.' + selector_type not in selector:
                selector[selector_key + '.' + selector_type] =\
                    [selector_option]
            else:
                selector[selector_key + '.' + selector_type].append(
                    selector_option)

        selectors = []
        for selector_type, selector_options in selector.items():
            selectors.append(selector_getter(
                selector_type, selector_options, dataset_config))

        return selectors

    @classmethod
    def from_config(cls, config):
        config_section = config.get('genotypeBrowser', None)
        if config_section is None:
            return False
        config_section = cls.parse(config_section)

        config_section['phenoFilters'] =\
            cls._get_pheno_filters(config_section)
        config_section['phenoColumns'] =\
            cls._get_pheno_columns(config_section)
        config_section['genotypeColumns'] =\
            cls._get_genotype_columns(config_section) + \
            config_section['phenoColumns']
        config_section['rolesColumns'] =\
            cls._get_in_roles_columns(config_section)
        config_section['previewColumnsSlots'] =\
            cls._get_column_slots(
                config_section.get('genotypeColumns', []),
                config_section.get('previewColumns', []))
        config_section['downloadColumnsSlots'] =\
            cls._get_column_slots(
                config_section.get('genotypeColumns', []),
                config_section.get('downloadColumns', []))

        config_section['columnLabels'] =\
            cls._get_column_labels(
                config_section.get('genotypeColumns', []))

        config_section['geneWeightsColumns'] =\
            cls._get_gene_weights_columns(
                config_section.get('genotypeColumns', []))

        people_group = cls._get_selectors(
            config_section, 'peopleGroup', cls._get_pedigree)
        if people_group:
            config_section['peopleGroup'] = people_group

        present_in_role = cls._get_selectors(
            config_section, 'presentInRole', cls._get_present_in_role)
        if present_in_role:
            config_section['presentInRole'] = present_in_role

        return GenotypeBrowserConfig(config_section)
