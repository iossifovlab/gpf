from box import Box

from dae.configuration.dae_config_parser import DAEConfigParser

from dae.variants.attributes import Role


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)


class GenotypeBrowserConfig(DAEConfigParser):

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
        'phenoFilters',
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
        'selectedPresentInRoleValues'
    ]

    @classproperty
    def PARSE_TO_LIST(cls):
        return {
            'phenoFilters': {
                'group': 'phenoFilters',
                'getter': cls._get_pheno_filter,
                'selected': 'phenoFilters.filters',
                'default': None
            }, 'phenoColumns': {
                'group': 'pheno',
                'getter': cls._get_pheno_column,
                'selected': 'pheno.columns',
                'default': []
            }, 'genotypeColumns': {
                'group': 'genotype',
                'getter': cls._get_genotype_column,
                'selected': 'genotype.columns',
                'default': []
            }, 'rolesColumns': {
                'group': 'inRoles',
                'getter': cls._get_in_roles_column,
                'selected': 'inRoles.columns',
                'default': []
            }, 'presentInRole': {
                'group': 'presentInRole',
                'getter': cls._get_present_in_role,
                'selected': 'selectedPresentInRoleValues',
                'default': []
            }
        }

    @staticmethod
    def _get_pheno_filter(
            pheno_filter_type, pheno_filter_options, study_config):
        pheno_filter = {}

        mf = study_config.get(pheno_filter_type + '.filter', None)
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

        pheno_filter['name'] = \
            study_config.get(pheno_filter_type + '.name', None)
        pheno_filter['id'] = pheno_filter['name']
        pheno_filter['measureType'] = \
            study_config.get(pheno_filter_type + '.type', None)
        pheno_filter['measureFilter'] = \
            Box(measure_filter, camel_killer_box=True)

        yield Box(pheno_filter, camel_killer_box=True)

    @classmethod
    def _get_pheno_column(
            cls, pheno_column_type, pheno_column_options, study_config):
        slots = cls._split_str_option_list(
            study_config.get(pheno_column_type + '.slots', None))

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

        pheno_column = {}

        _, pheno_column['id'] = cls._split_section(pheno_column_type)
        pheno_column['name'] = \
            study_config.get(pheno_column_type + '.name', None)
        pheno_column['slots'] = column_slots

        yield pheno_column

    @classmethod
    def _get_genotype_column(
            cls, genotype_column_type, genotype_column_options, study_config):
        slots = cls._split_str_option_list(
            study_config.get(genotype_column_type + '.slots', None))

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

        genotype_column = {}

        _, genotype_column['id'] = cls._split_section(genotype_column_type)
        genotype_column['name'] = \
            study_config.get(genotype_column_type + '.name', None)
        genotype_column['source'] = \
            study_config.get(genotype_column_type + '.source', None)
        genotype_column['slots'] = column_slots

        yield genotype_column

    @classmethod
    def _get_in_roles_column(
            cls, in_roles_column_type, in_roles_column_options, study_config):
        in_roles_column = {}

        _, in_roles_column['id'] = cls._split_section(in_roles_column_type)
        in_roles_column['roles'] = cls._split_str_option_list(
            study_config.get(in_roles_column_type + '.roles', None))
        in_roles_column['destination'] = study_config.get(
            in_roles_column_type + '.destination', in_roles_column['id'])

        yield in_roles_column

    @classmethod
    def _get_present_in_role(
            cls, present_in_role_type, present_in_role_options, study_config):
        present_in_role = {}

        present_in_role['name'] = \
            study_config.get(present_in_role_type + '.name', None)
        _, present_in_role['id'] = cls._split_section(present_in_role_type)
        present_in_role['roles'] = \
            [
                Role.from_name(el.strip()).display_name
                for el in study_config.get(
                   present_in_role_type + '.roles').split(',')
            ]

        yield present_in_role

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
        config = super(GenotypeBrowserConfig, cls).parse(config)

        config_section = config.get('genotypeBrowser', None)
        if config_section is None:
            return False

        print(config_section.keys())

        config_section['genotypeColumns'] += config_section['phenoColumns']
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

        return config_section

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
