from box import Box

from dae.configuration.config_parser_base import ConfigParserBase

from dae.variants.attributes import Role, Inheritance


def verify_inheritance_types(str_list):
    for string in str_list:
        assert Inheritance.from_name(string)
    return str_list


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
        'previewColumns',
        'downloadColumns',
        'selectedPhenoColumnValues',
        'familyFilters',
        'selectedPhenoFiltersValues',
        'selectedGenotypeColumnValues',
        'selectedInRolesValues',
        'selectedPresentInRoleValues',
        'inheritanceTypeFilter',
        'selectedInheritanceTypeFilterValues',
    ]

    FILTER_SELECTORS = {
        'phenoFilters': 'selectedPhenoFiltersValues',
        'pheno': 'selectedPhenoColumnValues',
        'genotype': 'selectedGenotypeColumnValues',
        'inRoles': 'selectedInRolesValues',
        'presentInRole': 'selectedPresentInRoleValues'
    }

    VERIFY_VALUES = {
        'inheritanceTypeFilter': verify_inheritance_types,
        'selectedInheritanceTypeFilterValues': verify_inheritance_types,
    }

    INCLUDE_PROPERTIES = (
        'hasCNV',
        'hasComplex',
        'hasStudyTypes',
        'hasStudyFilters',
        'hasFamilyFilters',
        'hasPresentInRole',
        'hasPresentInChild',
        'hasPresentInParent',
        'hasPedigreeSelector',
        'hasGraphicalPreview',
        'inheritanceTypeFilter',
        'selectedInheritanceTypeFilterValues',
        'familyFilters',
        'selectedPhenoFiltersValues',
        'name',
        'measureType',
        'filter',
        'selectedPresentInRoleValues',
        'id',
        'name',
        'roles',
        'selectedGenotypeColumnValues',
        'id',
        'name',
        'source',
        'slots',
        'selectedPhenoColumnValues',
        'id',
        'name',
        'slots',
        'inRoles',
        'previewColumns',
        'downloadColumns',
        'destination',
    )

    @classmethod
    def _parse_pheno_filter(cls, pheno_filters):
        if pheno_filters is None:
            return None

        for pheno_filter in pheno_filters.values():
            filter_type, role, *measure = \
                cls._split_str_option_list(pheno_filter.filter, separator=':')
            measure = measure[0] if measure else None

            measure_filter = {
                'filterType': filter_type,
                'role': role
            }
            if measure is not None:
                measure_filter['measure'] = measure

            pheno_filter.id = pheno_filter.name
            pheno_filter.measureFilter = measure_filter

        return list(pheno_filters.values())

    @classmethod
    def _parse_pheno_column(cls, pheno_columns):
        for pheno in pheno_columns.values():
            slots = cls._split_str_option_list(pheno.slots)

            column_slots = []
            for slot in slots:
                role, source, label, *label_format = \
                    cls._split_str_option_list(slot, separator=':')
                label_format = label_format[0] if label_format else '%s'

                column_slots.append({
                    'id': f'{pheno.id}.{label}',
                    'name': label,
                    'role': role,
                    'measure': source,
                    'source': '{}.{}'.format(role, source),
                    'format': label_format
                })

            pheno.slots = column_slots

        return pheno_columns

    @classmethod
    def _parse_genotype_column(cls, genotype_columns):
        for genotype_column in genotype_columns.values():
            slots = cls._split_str_option_list(genotype_column.slots)

            column_slots = []
            for slot in slots or []:
                source, *slot_arr = \
                    cls._split_str_option_list(slot, separator=':')
                label = slot_arr[0] if len(slot_arr) > 0 else source
                label_format = slot_arr[1] if len(slot_arr) > 1 else '%s'

                column_slots.append({
                    'id': f'{genotype_column.id}.{label}',
                    'name': label,
                    'source': source,
                    'format': label_format
                })

            genotype_column.slots = column_slots

        return genotype_columns

    @classmethod
    def _parse_in_role_columns(cls, in_roles):
        for in_role in in_roles.values():
            in_role.roles = [
                Role.from_name(el)
                for el in cls._split_str_option_list(in_role.roles)
            ]
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
    def _parse_column_slots(genotype_columns, selected_columns):
        column_slots = {}
        for column in selected_columns:
            genotype_column = genotype_columns.get(column, None)

            if not genotype_column:
                continue

            if genotype_column.get('source', None):
                column_slots[genotype_column['id']] = {
                    'id': genotype_column['id'],
                    'name': genotype_column['name'],
                    'source': genotype_column['source']
                }

            for slot in genotype_column.get('slots', []):
                if slot['source'] is not None:
                    column_slots[slot['id']] = {
                        'id': slot['id'],
                        'name': slot['name'],
                        'source': slot['source']
                    }

        return column_slots

    @staticmethod
    def _parse_gene_weight_columns(genotype_columns):
        gene_weight_columns = genotype_columns.get('weights', None)

        if not gene_weight_columns:
            return []

        return [gwc['source'] for gwc in gene_weight_columns.get('slots', [])]

    @classmethod
    def _parse_columns(cls, config):
        config.genotypeColumns = \
            cls._parse_genotype_column(config.get('genotype', {}))
        config.pheno_columns = cls._parse_pheno_column(config.get('pheno', {}))
        config.genotypeColumns.update(config.pheno_columns)

        config.preview_column_slots = cls._parse_column_slots(
            config.genotypeColumns, config.get('previewColumns', [])
        )
        config.download_column_slots = cls._parse_column_slots(
            config.genotypeColumns, config.get('downloadColumns', [])
        )
        if 'pedigree' in config.download_column_slots:
            config.download_column_slots.pop('pedigree')

        config.gene_weight_column_sources = \
            cls._parse_gene_weight_columns(config.genotypeColumns)

        config.in_role_columns = \
            cls._parse_in_role_columns(config.get('inRoles', {}))

        config.genotypeColumns = list(config.genotypeColumns.values())
        config.pheno_column_slots = [
            s
            for pc in config.pop('pheno_columns').values()
            for s in pc['slots']
        ]

        return config

    @classmethod
    def parse(cls, config):
        if cls.SECTION not in config:
            return None
        config = super(GenotypeBrowserConfigParser, cls).parse(config)

        config_section = config.genotype_browser
        if config_section is None:
            return False

        config_section.phenoFilters = \
            cls._parse_pheno_filter(config_section.phenoFilters)

        config_section = cls._parse_columns(config_section)

        config_section.presentInRole = \
            cls._parse_present_in_role(config_section.get('presentInRole', {}))

        if config_section.selected_inheritance_type_filter_values:
            assert config_section.inheritance_type_filter
            assert all([
                inheritance_type in config_section.inheritance_type_filter
                for inheritance_type
                in config_section.selected_inheritance_type_filter_values
            ])

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
            'previewColumns', 'genotypeColumns', 'phenoFilters',
            'familyFilters', 'presentInRole', 'downloadColumns',
            'inheritanceTypeFilter', 'selectedInheritanceTypeFilterValues',
        ]

    @classmethod
    def get_config_description(cls, config):
        keys = cls._get_description_keys()
        config = config.to_dict()

        result = {key: config.get(key, None) for key in keys}

        return result
