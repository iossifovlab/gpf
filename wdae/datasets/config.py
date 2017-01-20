'''
Created on Jan 20, 2017

@author: lubo
'''
import ConfigParser

from Config import Config


class DatasetConfig(object):

    @staticmethod
    def split_section(section):
        index = section.find('.')
        if index == -1:
            return (section, None)
        section_type = section[:index]
        section_name = section[index + 1:]
        return (section_type, section_name)

    def __init__(self, **kwargs):
        super(DatasetConfig, self).__init__()
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
                section_name = self.config.get(section, 'name')
                res.append({
                    'id': section_id,
                    'name': section_name
                })
        return res

    def get_phenotypes(self, phenotype_ids=None):
        res = []
        for section in self.config.sections():
            (section_type, section_id) = self.split_section(section)
            if section_id is None:
                continue
            if section_type != 'phenotype':
                continue
            if phenotype_ids and (section_id not in phenotype_ids):
                continue
            name = self.config.get(section, 'name')
            color = self.config.get(section, 'color')
            res.append({
                'id': section_id,
                'name': name,
                'color': color,
            })
        return res

    def _get_boolean(self, section, option):
        res = False
        if self.config.has_option(section, option):
            res = self.config.getboolean(section, option)
        return res

    def _get_string(self, section, option):
        res = None
        if self.config.has_option(section, option):
            res = self.config.get(section, option)
        return res

    def _get_genotype_browser(self, section):
        if not self._get_boolean(section, 'genotypeBrowser'):
            return None
        main_form = self._get_string(section, 'genotypeBrowser.mainForm')
        has_denovo = self._get_boolean(section, 'genotypeBrowser.hasDenovo')
        has_transmitted = \
            self._get_boolean(section, 'genotypeBrowser.hasTransmitted')
        has_cnv = self._get_boolean(section, 'genotypeBrowser.hasCNV')
        study_types = self._get_string(section, 'genotypeBrowser.studyTypes')
        if study_types:
            study_types = [st for st in study_types.split(',')]

        advanced_family_filters = \
            self._get_boolean(section, 'genotypeBrowser.advancedFamilyFilter')

        return {
            'mainForm': main_form,
            'hasDenovo': has_denovo,
            'hasTransmitted': has_transmitted,
            'hasCNV': has_cnv,
            'studyTypes': study_types,
            'advancedFamilyFilters': advanced_family_filters
        }

    def get_dataset(self, dataset_id):
        section = 'dataset.{}'.format(dataset_id)
        if not self.config.has_section(section):
            return None

        name = self.config.get(section, 'name')
        phenotypes = self.config.get(section, 'phenotypes').split(',')
        phenotypes = self.get_phenotypes(phenotype_ids=set(phenotypes))

        studies = self.config.get(section, 'studies')

        pheno_db = self._get_string(section, 'phenoDB')
        enrichment_tool = self._get_boolean(section, 'enrichmentTool')
        pheno_geno_tool = self._get_boolean(section, 'phenoGenoTool')
        phenotype_browser = self._get_boolean(section, 'phenotypeBrowser')
        genotype_browser = self._get_genotype_browser(section)

        return {
            'id': dataset_id,
            'name': name,
            'studies': studies,
            'phenotypes': phenotypes,
            'phenoDB': pheno_db,
            'enrichmentTool': enrichment_tool,
            'phenotypeGenotypeTool': pheno_geno_tool,
            'phenotypeBrowser': phenotype_browser,
            'genotypeBrowser': genotype_browser,
        }
