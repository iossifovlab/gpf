from box import Box

from dae.configuration.config_parser_base import ConfigParserBase

from dae.variants.attributes import Role


class GenotypeBrowserConfigParser(ConfigParserBase):

    SECTION = 'genotypeBrowser'

    CAST_TO_BOOL = (
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
        'baseColumns',
        'basePreviewColumns',
        'baseDownloadColumns',
        'previewColumns',
        'downloadColumns',
        'pheno.columns',
        'familyFilters',
        'phenoFilters.filters',
        'genotype.columns',
        'inRoles.columns',
        'selectedPresentInRoleValues',
        'roles',
        'columns',
    ]

    @classmethod
    def _get_pheno_filter(cls, config):
        if config is None:
            return None

        pheno_filters = []

        selected_filters = cls._split_str_option_list(config.filters)

        for pheno_filter_id, pheno_filter in config.items():
            if not isinstance(pheno_filter, dict):
                continue
            if selected_filters and pheno_filter_id not in selected_filters:
                continue

            mf = pheno_filter.filter
            mf = mf.split(':')
            if mf[0] == 'single':
                filter_type, role, measure = mf
                measure_filter = {
                    'filterType': filter_type,
                    'role': role,
                    'measure': measure
                }
            elif mf[0] == 'multi':
                filter_type, role = mf
                measure_filter = {
                    'filterType': filter_type,
                    'role': role
                }

            pheno_filter['id'] = pheno_filter['name']
            pheno_filter['measureType'] = pheno_filter.pop('type', None)
            pheno_filter['measureFilter'] = measure_filter

            pheno_filters.append(pheno_filter)

        return pheno_filters

    @classmethod
    def _get_pheno_column(cls, config):
        pheno_columns = []

        selected_columns = cls._split_str_option_list(config.columns)

        for pheno_id, pheno in config.items():
            if not isinstance(pheno, dict):
                continue
            if selected_columns and pheno_id not in selected_columns:
                continue

            slots = cls._split_str_option_list(pheno.slots)

            column_slots = []
            for slot in slots:
                role, source, label = slot.split(':')
                column_slots.append(
                    {
                        'id': '{}.{}'.format(role, source),
                        'name': label,
                        'role': role,
                        'measure': source,
                        'source': '{}.{}'.format(role, source),
                    })

            pheno['id'] = pheno_id
            pheno['slots'] = column_slots

            pheno_columns.append(pheno)

        return pheno_columns

    @classmethod
    def _get_genotype_column(cls, config):
        genotype_column = []

        selected_columns = cls._split_str_option_list(config.columns)

        for genotype_id, genotype in config.items():
            if not isinstance(genotype, dict):
                continue
            if selected_columns and genotype_id not in selected_columns:
                continue

            slots = cls._split_str_option_list(genotype.slots)

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
                        'id': source,
                        'name': label,
                        'source': source,
                        'format': label_format
                    })

            genotype['id'] = genotype_id
            genotype['slots'] = column_slots

            genotype_column.append(genotype)

        return genotype_column

    @classmethod
    def _get_in_roles_column(cls, in_roles):
        in_roles_column = []

        selected_in_roles = cls._split_str_option_list(
            in_roles.get('columns', None))

        for in_role_id, in_role in in_roles.items():
            if not isinstance(in_role, dict):
                continue
            if selected_in_roles and in_role_id not in selected_in_roles:
                continue

            in_role['id'] = in_role_id
            in_role['roles'] = cls._split_str_option_list(in_role['roles'])
            in_role['destination'] = in_role.get('destination', in_role['id'])

            in_roles_column.append(in_role)

        return in_roles_column

    @classmethod
    def _get_present_in_role(cls, config):
        present_in_role = config.get('presentInRole', {})
        selected_present_in_role = config.selected_present_in_role_values

        present_in_roles = []

        for pir_id, pir in present_in_role.items():
            if selected_present_in_role and \
                    pir_id not in selected_present_in_role:
                continue

            pir['id'] = pir_id
            pir['roles'] = [
                Role.from_name(el.strip()).display_name
                for el in cls._split_str_option_list(pir['roles'])
            ]

            present_in_roles.append(pir)

        config['presentInRole'] = present_in_roles

        return config

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

    @classmethod
    def parse(cls, config):
        config = super(GenotypeBrowserConfigParser, cls).parse(config)

        config_section = config.get('genotypeBrowser', None)
        if config_section is None:
            return False

        config_section['phenoFilters'] = \
            cls._get_pheno_filter(config_section.get('phenoFilters', None))

        config_section['genotypeColumns'] = \
            cls._get_genotype_column(config_section.pop('genotype', {}))
        config_section['phenoColumns'] = \
            cls._get_pheno_column(config_section.pop('pheno', {}))

        config_section['genotypeColumns'] += config_section['phenoColumns']
        config_section['previewColumnsSlots'] = \
            cls._get_column_slots(
                config_section.get('genotypeColumns', []),
                config_section.get('previewColumns', []))
        config_section['downloadColumnsSlots'] = \
            cls._get_column_slots(
                config_section.get('genotypeColumns', []),
                config_section.get('downloadColumns', []))

        config_section['columnLabels'] = \
            cls._get_column_labels(
                config_section.get('genotypeColumns', []))

        config_section['geneWeightsColumns'] = \
            cls._get_gene_weights_columns(
                config_section.get('genotypeColumns', []))

        config_section = cls._get_present_in_role(config_section)
        config_section['rolesColumns'] = \
            cls._get_in_roles_column(config_section.get('inRoles', {}))

        return Box(
            config_section, camel_killer_box=True, default_box=True,
            default_box_attr=None
        )

    @staticmethod
    def _get_description_keys():
        return [
            'hasPedigreeSelector', 'hasPresentInChild', 'hasPresentInParent',
            'hasPresentInRole', 'hasCNV', 'hasComplex', 'hasFamilyFilters',
            'hasStudyFilters', 'hasStudyTypes', 'hasGraphicalPreview',
            'previewColumns', 'rolesFilterOptions', 'genotypeColumns',
            'phenoFilters', 'familyFilters', 'presentInRole',
            'phenoColumns', 'downloadColumns'
        ]

    @classmethod
    def get_config_description(cls, config):
        keys = cls._get_description_keys()
        config = config.to_dict()

        result = {key: config.get(key, None) for key in keys}

        return result
