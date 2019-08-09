import os

from dae.configuration.dae_config_parser import DAEConfigParser


class DAEConfig(object):

    HDFS_SECTION = 'HDFS'
    HDFS_HOST = 'host'
    HDFS_PORT = 'port'
    HDFS_BASE_DIR = 'baseDir'

    IMPALA_SECTION = 'Impala'
    IMPALA_HOST = 'host'
    IMPALA_PORT = 'port'
    IMPALA_DB = 'db'

    DIR_NAME = 'dir'
    CONF_FILE = 'confFile'
    STUDIES_SECTION = 'studiesDB'
    DATASETS_SECTION = 'datasetsDB'
    PHENO_SECTION = 'phenoDB'
    GENE_INFO_SECTION = 'geneInfoDB'
    GENOMIC_SCORES_SECTION = 'genomicScoresDB'
    GENOMES_SECTION = 'genomesDB'
    ANNOTATION_SECTION = 'annotation'
    DEFAULT_CONFIGURATION_SECTION = 'defaultConfiguration'

    def __init__(
        self, dae_data_dir, dae_scores_hg19_dir, dae_scores_hg38_dir,
            sections):
        self._dae_data_dir = dae_data_dir
        self._dae_scores_hg19_dir = dae_scores_hg19_dir
        self._dae_scores_hg38_dir = dae_scores_hg38_dir
        self.sections = sections

    @classmethod
    def make_config(
        cls, dae_data_dir=None, dae_scores_hg19_dir=None,
        dae_scores_hg38_dir=None, dae_conf_filename="DAE.conf",
        environment_override=True, impala_host=None, impala_port=None,
            impala_db=None, hdfs_host=None, hdfs_port=None):
        if dae_data_dir is None:
            dae_data_dir = os.environ.get('DAE_DB_DIR', None)
        assert dae_data_dir is not None
        dae_data_dir = os.path.abspath(dae_data_dir)
        assert os.path.exists(dae_data_dir)
        assert os.path.isdir(dae_data_dir)

        if environment_override:
            if dae_scores_hg19_dir is None:
                dae_scores_hg19_dir = os.environ.get(
                    'DAE_GENOMIC_SCORES_HG19', None)

            if dae_scores_hg38_dir is None:
                dae_scores_hg38_dir = os.environ.get(
                    'DAE_GENOMIC_SCORES_HG38', None)

            if impala_host is None:
                impala_host = os.environ.get('DAE_IMPALA_HOST', None)

            if impala_port is None:
                impala_port = os.environ.get('DAE_IMPALA_PORT', None)

            if impala_db is None:
                impala_db = os.environ.get('DAE_IMPALA_DB', None)

            if hdfs_host is None:
                hdfs_host = os.environ.get('DAE_HDFS_HOST', None)

            if hdfs_port is None:
                hdfs_port = os.environ.get('DAE_HDFS_PORT', None)

        filename = os.path.join(dae_data_dir, dae_conf_filename)
        sections = DAEConfigParser.read_file_configuration(
            filename,
            dae_data_dir,
            {'wd': dae_data_dir, 'work_dir': dae_data_dir}
        )
        assert sections is not None

        if dae_scores_hg19_dir is not None:
            dae_scores_hg19_dir = os.path.abspath(dae_scores_hg19_dir)
            assert os.path.exists(dae_scores_hg19_dir)
            assert os.path.isdir(dae_scores_hg19_dir)
            if sections.get(cls.GENOMIC_SCORES_SECTION, None) is None:
                sections[cls.GENOMIC_SCORES_SECTION] = {}
            sections[cls.GENOMIC_SCORES_SECTION]['scores_hg19_dir'] = \
                dae_scores_hg19_dir

        if dae_scores_hg38_dir is not None:
            dae_scores_hg38_dir = os.path.abspath(dae_scores_hg38_dir)
            assert os.path.exists(dae_scores_hg38_dir)
            assert os.path.isdir(dae_scores_hg38_dir)
            if sections.get(cls.GENOMIC_SCORES_SECTION, None) is None:
                sections[cls.GENOMIC_SCORES_SECTION] = {}
            sections[cls.GENOMIC_SCORES_SECTION]['scores_hg38_dir'] = \
                dae_scores_hg38_dir

        if impala_host is not None:
            if sections.get(cls.IMPALA_SECTION, None) is None:
                sections[cls.IMPALA_SECTION] = {}
            sections[cls.IMPALA_SECTION][cls.IMPALA_HOST] = impala_host

        if impala_port is not None:
            if sections.get(cls.IMPALA_SECTION, None) is None:
                sections[cls.IMPALA_SECTION] = {}
            sections[cls.IMPALA_SECTION][cls.IMPALA_PORT] = impala_port

        if impala_db is not None:
            if sections.get(cls.IMPALA_SECTION, None) is None:
                sections[cls.IMPALA_SECTION] = {}
            sections[cls.IMPALA_SECTION][cls.IMPALA_DB] = impala_db

        if hdfs_host is not None:
            if sections.get(cls.HDFS_SECTION, None) is None:
                sections[cls.HDFS_SECTION] = {}
            sections[cls.HDFS_SECTION][cls.HDFS_HOST] = hdfs_host

        if hdfs_port is not None:
            if sections.get(cls.HDFS_SECTION, None) is None:
                sections[cls.HDFS_SECTION] = {}
            sections[
                cls.HDFS_SECTION][cls.HDFS_PORT] = hdfs_port

        return DAEConfig(
            dae_data_dir, dae_scores_hg19_dir, dae_scores_hg38_dir, sections
        )

    def _get_config_value(self, section_id, attr_name, default_value=None):
        if section_id not in list(self.sections.keys()):
            return default_value
        return self.sections.get(section_id).get(attr_name, default_value)

    def impala_section(self):
        return self.sections.get(self.IMPALA_SECTION)

    @property
    def impala_db(self):
        return self._get_config_value(
            self.IMPALA_SECTION, self.IMPALA_DB, "gpf_variant_db")

    @property
    def impala_host(self):
        return self._get_config_value(
            self.IMPALA_SECTION, self.IMPALA_HOST, None)

    @property
    def impala_port(self):
        return int(self._get_config_value(
            self.IMPALA_SECTION, self.IMPALA_PORT, 21050))

    def hdfs_section(self):
        return self.sections.get(self.HDFS_SECTION)

    @property
    def hdfs_base_dir(self):
        return self._get_config_value(
            self.HDFS_SECTION, self.HDFS_BASE_DIR, "/tmp")

    @property
    def hdfs_host(self):
        return self._get_config_value(self.HDFS_SECTION, self.HDFS_HOST, None)

    @property
    def hdfs_port(self):
        return int(self._get_config_value(
            self.HDFS_SECTION, self.HDFS_PORT, 0))

    @property
    def dae_data_dir(self):
        return self._dae_data_dir

    def studies_section(self):
        return self.sections.get(self.STUDIES_SECTION)

    @property
    def studies_dir(self):
        return self._get_config_value(self.STUDIES_SECTION, self.DIR_NAME)

    @property
    def studies_conf(self):
        return self._get_config_value(self.STUDIES_SECTION, self.CONF_FILE)

    def datasets_section(self):
        return self.sections.get(self.DATASETS_SECTION)

    @property
    def datasets_dir(self):
        return self._get_config_value(self.DATASETS_SECTION, self.DIR_NAME)

    @property
    def datasets_conf(self):
        return self._get_config_value(self.DATASETS_SECTION, self.CONF_FILE)

    def pheno_section(self):
        return self.sections.get(self.PHENO_SECTION)

    @property
    def pheno_dir(self):
        return self._get_config_value(self.PHENO_SECTION, self.DIR_NAME)

    @property
    def pheno_conf(self):
        return str(self._get_config_value(self.PHENO_SECTION, self.CONF_FILE))

    def gene_info_section(self):
        return self.sections.get(self.GENE_INFO_SECTION)

    @property
    def gene_info_dir(self):
        return self._get_config_value(self.GENE_INFO_SECTION, self.DIR_NAME)

    @property
    def gene_info_conf(self):
        return self._get_config_value(self.GENE_INFO_SECTION, self.CONF_FILE)

    def genomic_scores_section(self):
        return self.sections.get(self.GENOMIC_SCORES_SECTION)

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
            self.GENOMIC_SCORES_SECTION, 'scores_hg19_dir', None)

    @property
    def genomic_scores_hg38_dir(self):
        return self._get_config_value(
            self.GENOMIC_SCORES_SECTION, 'scores_hg38_dir', None)

    def annotation_section(self):
        return self.sections.get(self.ANNOTATION_SECTION)

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
        return self.sections.get(self.GENOMES_SECTION)

    @property
    def genomes_dir(self):
        return self._get_config_value(
            self.GENOMES_SECTION, self.DIR_NAME)

    @property
    def genomes_conf(self):
        return self._get_config_value(
            self.GENOMES_SECTION, self.CONF_FILE)

    def default_configuration_section(self):
        return self.sections.get(
            self.DEFAULT_CONFIGURATION_SECTION)

    @property
    def default_configuration_conf(self):
        return self._get_config_value(
            self.DEFAULT_CONFIGURATION_SECTION, self.CONF_FILE)
