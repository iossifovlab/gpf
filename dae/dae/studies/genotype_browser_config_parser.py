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
        'selectedPhenoValues',
        'familyFilters',
        'selectedPhenoFiltersValues',
        'selectedGenotypeValues',
        'selectedInRolesValues',
        'selectedPresentInRoleValues',
        'roles',
        'columns',
    ]

    FILTER_SELECTORS = {
        'phenoFilters': 'selectedPhenoFiltersValues',
        'pheno': 'selectedPhenoValues',
        'genotype': 'selectedGenotypeValues',
        'inRoles': 'selectedInRolesValues',
        'presentInRole': 'selectedPresentInRoleValues'
    }

    @classmethod
    def _parse_pheno_filter(cls, pheno_filters):
        if pheno_filters is None:
            return None

        for pheno_filter in pheno_filters.values():
            mf = pheno_filter.filter
            mf = cls._split_str_option_list(mf, separator=':')
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

            pheno_filter.id = pheno_filter.name
            pheno_filter.measureFilter = measure_filter

        return list(pheno_filters.values())

    @classmethod
    def _parse_pheno_column(cls, pheno_columns):
        for pheno in pheno_columns.values():
            slots = cls._split_str_option_list(pheno.slots)

            column_slots = []
            for slot in slots:
                role, source, label = \
                    cls._split_str_option_list(slot, separator=':')
                column_slots.append(
                    {
                        'id': '{}.{}'.format(role, source),
                        'name': label,
                        'role': role,
                        'measure': source,
                        'source': '{}.{}'.format(role, source),
                    })

            pheno.slots = column_slots

        return list(pheno_columns.values())

    @classmethod
    def _parse_genotype_column(cls, genotype_columns):
        for genotype_column in genotype_columns.values():
            slots = cls._split_str_option_list(genotype_column.slots)

            column_slots = []
            for slot in slots or []:
                slot_arr = cls._split_str_option_list(slot, separator=':')
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

            genotype_column.slots = column_slots

        return list(genotype_columns.values())

    @classmethod
    def _parse_in_roles_column(cls, in_roles):
        for in_role in in_roles.values():
            in_role.roles = cls._split_str_option_list(in_role.roles)
            in_role.destination = in_role.get('destination', in_role.id)

        return list(in_roles.values())

    @classmethod
    def _parse_present_in_role(cls, present_in_roles):
        for pir in present_in_roles.values():
            pir.roles = [
                Role.from_name(el).display_name
                for el in cls._split_str_option_list(pir.roles)
            ]

        return list(present_in_roles.values())

    @staticmethod
    def _parse_column_slots(genotype_columns, columns):
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
    def _parse_column_labels(genotype_columns):
        column_labels = {}
        for gc in genotype_columns:
            if 'source' in gc and gc['source'] is not None:
                column_labels[gc['source']] = gc['name']

            for slot in gc['slots']:
                if slot['source'] is not None:
                    column_labels[slot['source']] = slot['name']

        return column_labels

    @staticmethod
    def _parse_gene_weights_columns(genotype_columns):
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
        if cls.SECTION not in config:
            return None
        config = super(GenotypeBrowserConfigParser, cls).parse(config)

        config_section = config.get('genotypeBrowser', None)
        if config_section is None:
            return False

        config_section['phenoFilters'] = \
            cls._parse_pheno_filter(config_section.get('phenoFilters', None))

        config_section['genotypeColumns'] = \
            cls._parse_genotype_column(config_section.get('genotype', {}))
        config_section['phenoColumns'] = \
            cls._parse_pheno_column(config_section.get('pheno', {}))

        config_section['genotypeColumns'] += config_section['phenoColumns']
        config_section['previewColumnsSlots'] = \
            cls._parse_column_slots(
                config_section.get('genotypeColumns', []),
                config_section.get('previewColumns', []))
        config_section['downloadColumnsSlots'] = \
            cls._parse_column_slots(
                config_section.get('genotypeColumns', []),
                config_section.get('downloadColumns', []))

        config_section['columnLabels'] = \
            cls._parse_column_labels(
                config_section.get('genotypeColumns', []))

        config_section['geneWeightsColumns'] = \
            cls._parse_gene_weights_columns(
                config_section.get('genotypeColumns', []))

        config_section['presentInRole'] = \
            cls._parse_present_in_role(config_section.get('presentInRole', {}))
        config_section['rolesColumns'] = \
            cls._parse_in_roles_column(config_section.get('inRoles', {}))

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
