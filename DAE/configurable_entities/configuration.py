import os

from configurable_entities.configurable_entity_definition import\
    ConfigurableEntityDefinition
from configurable_entities.configurable_entity_config import \
    ConfigurableEntityConfig


class ConfigSectionConfig(ConfigurableEntityConfig):

    def __init__(self, config, *args, **kwargs):
        super(ConfigSectionConfig, self).__init__(config, *args, **kwargs)

    @classmethod
    def from_config(cls, config_section, section=None):
        section_config = config_section
        return ConfigSectionConfig(section_config)


class ConfigSectionDefinition(ConfigurableEntityDefinition):

    def __init__(self, config_path, work_dir):
        super(ConfigSectionDefinition, self).__init__()
        if work_dir is None:
            work_dir = os.environ.get("DAE_DB_DIR")
        assert work_dir is not None

        self.single_file_configurable_entity_definition(
            config_path, work_dir, ConfigSectionConfig, 'section_name',
            {'wd': work_dir, 'work_dir': work_dir})

    @property
    def section_ids(self):
        return self.configurable_entity_ids()

    def get_section_config(self, section_id):
        return self.get_configurable_entity_config(section_id)

    def get_all_section_configs(self):
        return self.get_all_configurable_entity_configs()

    def get_all_section_names(self):
        return self.get_all_configurable_entity_names()


class AnnotatorConfig(ConfigurableEntityConfig):
    def __init__(self, config, *args, **kwargs):
        super(AnnotatorConfig, self).__init__(config, *args, **kwargs)

    @classmethod
    def from_config(cls, config_section, section=None):
        section_config = config_section
        return AnnotatorConfig(section_config)


class AnnotatorDefinition(ConfigurableEntityDefinition):

    def __init__(self, config_path, work_dir):
        super(AnnotatorDefinition, self).__init__()

        self.single_file_configurable_entity_definition(
            config_path, work_dir, ConfigSectionConfig, 'section_name',
            {'wd': work_dir, 'work_dir': work_dir})

    @property
    def annotation_ids(self):
        return self.configurable_entity_ids()

    def get_annotator_config(self, section_id):
        return self.get_configurable_entity_config(section_id)

    def get_all_annotator_configs(self):
        return self.get_all_configurable_entity_configs()


class DAEConfig(object):

    DIR_NAME = 'dir'
    CONF_FILE = 'confFile'
    PHENO_SECTION = 'phenoDB'
    GENE_INFO_SECTION = 'geneInfoDB'
    GENOMIC_SCORES_SECTION = 'genomicScoresDB'
    GENOMES_SECTION = 'genomesDB'
    ANNOTATION_SECTION = 'annotation'

    def __init__(self, dae_data_dir=None, dae_conf_filename="DAE.conf"):
        if dae_data_dir is None:
            dae_data_dir = os.environ.get('DAE_DB_DIR', None)
        self._dae_data_dir = os.path.abspath(dae_data_dir)
        self.dae_conf_filename = dae_conf_filename

        filename = os.path.join(self.dae_data_dir, self.dae_conf_filename)
        self.sections = ConfigSectionDefinition(
            filename, work_dir=self.dae_data_dir
        )
        assert self.sections is not None

    def _get_config_value(self, section_name, attr_name):
        if section_name not in self.sections.get_all_section_names():
            return None
        return self.sections.get_section_config(section_name).get(attr_name)

    @property
    def dae_data_dir(self):
        return self._dae_data_dir

    def pheno_section(self):
        return self.sections.get_section_config(self.PHENO_SECTION)

    @property
    def pheno_dir(self):
        return self._get_config_value(self.PHENO_SECTION, self.DIR_NAME)

    @property
    def pheno_conf(self):
        return self._get_config_value(self.PHENO_SECTION, self.CONF_FILE)

    def gene_info_section(self):
        return self.sections.get_section_config(self.GENE_INFO_SECTION)

    @property
    def gene_info_dir(self):
        return self._get_config_value(self.GENE_INFO_SECTION, self.DIR_NAME)

    @property
    def gene_info_conf(self):
        return self._get_config_value(self.GENE_INFO_SECTION, self.CONF_FILE)

    def genomic_scores_section(self):
        return self.sections.get_section_config(self.GENOMIC_SCORES_SECTION)

    @property
    def genomic_scores_dir(self):
        return self._get_config_value(
            self.GENOMIC_SCORES_SECTION, self.DIR_NAME)

    @property
    def genomic_scores_conf(self):
        return self._get_config_value(
            self.GENOMIC_SCORES_SECTION, self.CONF_FILE)

    @property
    def genomic_scores_hg19_dir(self):
        return self._get_config_value(
            self.GENOMIC_SCORES_SECTION, 'scores_hg19_dir')

    @property
    def genomic_scores_hg38_dir(self):
        return self._get_config_value(
            self.GENOMIC_SCORES_SECTION, 'scores_hg38_dir')

    def annotation_section(self):
        return self.sections.get_section_config(self.ANNOTATION_SECTION)

    @property
    def annotation_dir(self):
        return self._get_config_value(
            self.ANNOTATION_SECTION, self.DIR_NAME)

    @property
    def annotation_conf(self):
        return self._get_config_value(
            self.ANNOTATION_SECTION, self.CONF_FILE)

    @property
    def annotation_defaults(self):
        return {
            'wd': self.dae_data_dir,
            'data_dir': self.dae_data_dir,
            'scores_hg19_dir': self.genomic_scores_hg19_dir,
            'scores_hg38_dir': self.genomic_scores_hg38_dir,
        }

    def genomes_section(self):
        return self.sections.get_section_config(self.GENOMES_SECTION)

    @property
    def genomes_dir(self):
        return self._get_config_value(
            self.GENOMES_SECTION, self.DIR_NAME)

    @property
    def genomes_conf(self):
        return self._get_config_value(
            self.GENOMES_SECTION, self.CONF_FILE)
