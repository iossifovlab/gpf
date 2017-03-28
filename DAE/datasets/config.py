'''
Created on Jan 20, 2017

@author: lubo
'''
import ConfigParser

from Config import Config
import collections
# from pprint import pprint


class PedigreeSelector(dict):

    def __init__(self, pedigree_id, **kwargs):
        self['id'] = pedigree_id
        self['domain'] = self._parse_domain(kwargs['domain'])
        self['default'] = self._parse_domain_value(kwargs['default'])
        self['source'] = kwargs['source']
        self['name'] = kwargs['name']
        self.id = self['id']
        self.name = self['name']
        self.domain = self['domain']
        self.default = self['default']

        self.values = dict([(v['id'], v) for v in self.domain])
        self['values'] = self.values

    def _parse_domain_value(self, value):
        (selector_id, selector_name, selector_color) = value.split(':')
        return {
            'id': selector_id,
            'name': selector_name,
            'color': selector_color,
        }

    def _parse_domain(self, domain):
        values = domain.split(',')
        result = [self._parse_domain_value(v.strip()) for v in values]
        return result

    def get_color(self, value_id):
        value = self.values.get(value_id, self.default)
        return value['color']

    def get_checked_values(self, **kwargs):
        checked = kwargs['pedigreeSelector']['checkedValues']
        checked = [v for v in checked if v in self.values]
        if len(checked) == len(self.values):
            return None
        return set(checked)


class DatasetsConfig(object):

    @staticmethod
    def split_section(section):
        index = section.find('.')
        if index == -1:
            return (section, None)
        section_type = section[:index]
        section_name = section[index + 1:]
        return (section_type, section_name)

    def __init__(self, **kwargs):
        super(DatasetsConfig, self).__init__()
        config = kwargs.get('config', None)

        if config:
            assert isinstance(config, ConfigParser.SafeConfigParser)
            self.config = config
        else:
            dae_config = Config()
            wd = dae_config.daeDir
            self.config = ConfigParser.SafeConfigParser({'wd': wd})
            self.config.read(dae_config.variantsDBconfFile)

    def get_datasets(self):
        res = []
        for section in self.config.sections():
            (section_type, section_id) = self.split_section(section)
            if section_id is None:
                continue
            if section_type == 'dataset':
                dataset = self.get_dataset_desc(section_id)
                res.append(dataset)
        return res

    def _get_boolean(self, section, option):
        res = False
        if self.config.has_option(section, option):
            res = self.config.getboolean(section, option)
        return res

    def _get_string(self, section, option, default_value=None):
        res = default_value
        if self.config.has_option(section, option):
            res = self.config.get(section, option)
        return res

    def _get_string_list(self, section, option, default_value=None):
        res = default_value
        if self.config.has_option(section, option):
            res = self.config.get(section, option)
            res = [r.strip() for r in res.split(',')]
        return res

    def _get_genotype_browser(self, section):
        if not self._get_boolean(section, 'genotypeBrowser'):
            return None
        main_form = self._get_string(section, 'genotypeBrowser.mainForm')
        has_denovo = self._get_boolean(section, 'genotypeBrowser.hasDenovo')
        has_transmitted = \
            self._get_boolean(section, 'genotypeBrowser.hasTransmitted')
        has_cnv = self._get_boolean(section, 'genotypeBrowser.hasCNV')
        has_present_in_child = self._get_boolean(
            section, 'genotypeBrowser.hasPresentInChild')
        has_present_in_parent = self._get_boolean(
            section, 'genotypeBrowser.hasPresentInParent')
        study_types = self._get_boolean(
            section, 'genotypeBrowser.hasStudyTypes')

        advanced_family_filters = \
            self._get_boolean(
                section, 'genotypeBrowser.hasAdvancedFamilyFilter')
        pedigree_selector = \
            self._get_boolean(
                section, 'genotypeBrowser.hasPedigreeSelector')
        pheno_columns = \
            self._get_genotype_browser_pheno_columns(section)
        pheno_filters = \
            self._get_genotype_browser_pheno_filters(section)

        return {
            'mainForm': main_form,
            'hasDenovo': has_denovo,
            'hasTransmitted': has_transmitted,
            'hasPresentInChild': has_present_in_child,
            'hasPresentInParent': has_present_in_parent,
            'hasCNV': has_cnv,
            'hasStudyTypes': study_types,
            'hasAdvancedFamilyFilters': advanced_family_filters,
            'hasPedigreeSelector': pedigree_selector,
            'phenoColumns': pheno_columns,
            'phenoFilters': pheno_filters,
        }

    def _get_genotype_browser_pheno_filters(self, section):
        result = []
        filters = self._get_string_list(
            section, 'genotypeBrowser.phenoFilters.filters')
        if not filters:
            return None

        for f in filters:
            pheno_filter = self._get_genotype_browser_pheno_filter(
                section, f)
            result.append(pheno_filter)
        return result

    def _get_genotype_browser_pheno_filter(self, section, f):
        prefix = 'genotypeBrowser.phenoFilters.{}'.format(f)
        name = self._get_string(
            section, '{}.{}'.format(prefix, 'name'))
        measure_type = self._get_string(
            section, '{}.{}'.format(prefix, 'type'))
        mf = self._get_string(
            section, '{}.{}'.format(prefix, 'filter'))
        mf = mf.split(':')
        if 'single' == mf[0]:
            filter_type, role, measure = mf
            measure_filter = {
                'filter_type': filter_type,
                'role': role,
                'measure': measure
            }
        elif 'multi' == mf[0]:
            filter_type, role = mf
            measure_filter = {
                'filter_type': filter_type,
                'role': role
            }
        return {
            'name': name,
            'measure_type': measure_type,
            'measure_filter': measure_filter
        }

    def _get_genotype_browser_pheno_columns(self, section):
        result = []
        columns = self._get_string_list(
            section, 'genotypeBrowser.pheno.columns')
        if not columns:
            return None

        for col in columns:
            column = self._get_genotype_browser_pheno_column(section, col)
            result.append(column)

        return result

    def _get_genotype_browser_pheno_column(self, section, col_id):
        prefix = 'genotypeBrowser.pheno.{}'.format(col_id)
        name = self._get_string(
            section, '{}.{}'.format(prefix, 'name'))
        slots = self._get_string_list(
            section, '{}.{}'.format(prefix, 'slots'))
        column = {}
        column['name'] = name
        column_slots = []
        for slot in slots:
            role, source, label = slot.split(':')
            column_slots.append(
                {
                    'role': role,
                    'source': source,
                    'name': label,
                    'id': '{}.{}'.format(name, label),
                })
        column['slots'] = column_slots
        return column

    def _get_enrichment_tool(self, section):
        if not self._get_boolean(section, 'enrichmentTool'):
            return None
        selector = self._get_string(section, 'enrichmentTool.selector')
        study_types = self._get_string(section, 'enrichmentTool.studyTypes')
        if study_types:
            study_types = [st.strip() for st in study_types.split(',')]
        return {
            'selector': selector,
            'studyTypes': study_types,
        }

    def _get_pedigree_selectors(self, section):
        params = collections.defaultdict(dict)

        options = self.config.options(section)
        for option in options:
            option_type, option_fullname = self.split_section(option)
            if option_type != 'pedigree':
                continue
            pedigree_type, pedigree_option = \
                self.split_section(option_fullname)
            pedigree = params[pedigree_type]
            value = self.config.get(section, option)
            pedigree[pedigree_option] = value

        if not params:
            return None
        result = []
        for key, value in params.items():
            pedigree = PedigreeSelector(key, **value)
            result.append(pedigree)
        return result

    def get_dataset_desc(self, dataset_id):
        section = 'dataset.{}'.format(dataset_id)
        if not self.config.has_section(section):
            return None

        name = self.config.get(section, 'name')

        studies = self.config.get(section, 'studies')

        visibility = self._get_string(section, 'visibility', 'AUTHENTICATED')

        study_types = self._get_string(section, 'studyTypes')
        if study_types:
            study_types = [st for st in study_types.split(',')]

        pheno_db = self._get_string(section, 'phenoDB')
        pheno_geno_tool = self._get_boolean(section, 'phenoGenoTool')
        phenotype_browser = self._get_boolean(section, 'phenotypeBrowser')
        genotype_browser = self._get_genotype_browser(section)
        enrichment_tool = self._get_enrichment_tool(section)

        pedigree_selectors = self._get_pedigree_selectors(section)

        return {
            'id': dataset_id,
            'name': name,
            'studies': studies,
            'studyTypes': study_types,
            'visibility': visibility,
            'phenoDB': pheno_db,
            'enrichmentTool': enrichment_tool,
            'phenotypeGenotypeTool': pheno_geno_tool,
            'phenotypeBrowser': phenotype_browser,
            'genotypeBrowser': genotype_browser,
            'pedigreeSelectors': pedigree_selectors,
        }
