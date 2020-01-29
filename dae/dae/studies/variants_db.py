from deprecation import deprecated

from dae.studies.study import GenotypeDataStudy, GenotypeDataGroup
from dae.studies.study_wrapper import StudyWrapper
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.study_config import study_config_schema


class VariantsDb(object):

    def __init__(
            self, dae_config, pheno_db, gene_weights_db, genomes_db,
            genotype_storage_factory):
        self.dae_config = dae_config

        assert pheno_db is not None
        assert gene_weights_db is not None
        assert genomes_db is not None
        assert genotype_storage_factory is not None

        self.pheno_db = pheno_db
        self.gene_weights_db = gene_weights_db
        self.genomes_db = genomes_db
        self.genotype_storage_factory = genotype_storage_factory

        defaults = {
            'values': {
                'dae_data_dir': self.dae_config.dae_data_dir
            }
        }
        if dae_config.default_study_config and \
                dae_config.default_study_config.conf_file:
            defaults['conf'] = dae_config.default_study_config.conf_file

        study_configs = GPFConfigParser.load_directory_configs(
            dae_config.studies_db.dir,
            study_config_schema
        )

        self.genotype_data_study_configs = {
            ds.id: ds
            for ds in study_configs
        }

        data_groups = GPFConfigParser.load_directory_configs(
            dae_config.datasets_db.dir,
            study_config_schema
        )

        self.genotype_data_group_configs = {
            dg.id: dg
            for dg in data_groups
        }

        self._genotype_data_study_cache = {}
        self._genotype_data_study_wrapper_cache = {}

        self._genotype_data_group_cache = {}
        self._genotype_data_group_wrapper_cache = {}

        self._configuration_check()

    def _configuration_check(self):
        studies_ids = set(self.get_genotype_studies_ids())
        genotype_data_group_ids = set(self.get_genotype_data_groups_ids())

        overlapping = studies_ids.intersection(genotype_data_group_ids)

        assert overlapping == set(), \
            "Overlapping studies and groups ids: {}".format(
                overlapping
            )

    def get_genotype_studies_ids(self):
        return list(self.genotype_data_study_configs.keys())

    def get_study_config(self, study_id):
        return self.genotype_data_study_configs.get(study_id)

    def get_study(self, study_id):
        self._load_study_cache({study_id})
        if study_id not in self._genotype_data_study_cache:
            return None

        return self._genotype_data_study_cache[study_id]

    def get_study_wdae_wrapper(self, study_id):
        self._load_study_cache({study_id})

        if study_id not in self._genotype_data_study_wrapper_cache:
            return None

        return self._genotype_data_study_wrapper_cache[study_id]

    def get_all_studies(self):
        self._load_study_cache()

        return list(self._genotype_data_study_cache.values())

    def get_all_studies_wrapper(self):
        self._load_study_cache()

        return list(self._genotype_data_study_wrapper_cache.values())

    def get_all_study_configs(self):
        self._load_study_cache()

        return [genotype_data_study.config
                for genotype_data_study
                in self._genotype_data_study_cache.values()]

    def get_genotype_data_groups_ids(self):
        return list(self.genotype_data_group_configs.keys())

    def get_genotype_data_group_config(self, genotype_data_group_id):
        return self.genotype_data_group_configs.get(genotype_data_group_id)

    def get_genotype_data_group(self, genotype_data_group_id):
        self._load_genotype_data_group_cache({genotype_data_group_id})

        if genotype_data_group_id not in self._genotype_data_group_cache:
            return None

        return self._genotype_data_group_cache[genotype_data_group_id]

    def get_genotype_data_group_wdae_wrapper(self, genotype_data_group_id):
        self._load_genotype_data_group_cache({genotype_data_group_id})

        if genotype_data_group_id not in \
                self._genotype_data_group_wrapper_cache:
            return None

        return self._genotype_data_group_wrapper_cache[genotype_data_group_id]

    def get_all_genotype_data_groups(self):
        self._load_genotype_data_group_cache()

        return list(self._genotype_data_group_cache.values())

    def get_all_genotype_data_groups_wrapper(self):
        self._load_genotype_data_group_cache()

        return list(self._genotype_data_group_wrapper_cache.values())

    def get_all_genotype_data_group_configs(self):
        self._load_genotype_data_group_cache()

        return [genotype_data_group.config
                for genotype_data_group
                in self._genotype_data_group_cache.values()]

    @deprecated(details="start using GPFInstance methods")
    def get_all_ids(self):
        return self.get_genotype_studies_ids() \
            + self.get_genotype_data_groups_ids()

    @deprecated(details="start using GPFInstance methods")
    def get_config(self, config_id):
        study_config = self.get_study_config(config_id)
        genotype_data_group_config = \
            self.get_genotype_data_group_config(config_id)
        return study_config if study_config else genotype_data_group_config

    @deprecated(details="start using GPFInstance methods")
    def get(self, object_id):
        genotype_data_study = self.get_study(object_id)
        genotype_data_group = self.get_genotype_data_group(object_id)
        return genotype_data_study if genotype_data_study \
            else genotype_data_group

    def get_wdae_wrapper(self, wdae_wrapper_id):
        study_wdae_wrapper = self.get_study_wdae_wrapper(wdae_wrapper_id)
        genotype_data_group_wdae_wrapper = \
            self.get_genotype_data_group_wdae_wrapper(wdae_wrapper_id)
        return study_wdae_wrapper\
            if study_wdae_wrapper else genotype_data_group_wdae_wrapper

    @deprecated(details="start using GPFInstance methods")
    def get_all_genotype_data(self):
        genotype_studies = self.get_all_studies()
        genotype_data_groups = self.get_all_genotype_data_groups()
        return genotype_studies + genotype_data_groups

    def get_all_genotype_data_wrappers(self):
        study_wrappers = self.get_all_studies_wrapper()
        genotype_data_group_wrappers = \
            self.get_all_genotype_data_groups_wrapper()
        return study_wrappers + genotype_data_group_wrappers

    def _load_study_cache(self, study_ids=None):
        if study_ids is None:
            study_ids = set(self.get_genotype_studies_ids())

        assert isinstance(study_ids, set)

        cached_ids = set(self._genotype_data_study_cache.keys())
        if study_ids != cached_ids:
            to_load = study_ids - cached_ids
            for study_id in to_load:
                self._load_study_in_cache(study_id)

    # def wrap_study(self, genotype_data_study):
    #     return StudyWrapper(genotype_data_study, self.pheno_db,
    #                         self.gene_weights_db)

    def _load_study_in_cache(self, study_id):
        conf = self.genotype_data_study_configs.get(study_id)
        if not conf:
            return

        genotype_data_study = self.make_genotype_data_study(conf)
        if genotype_data_study is None:
            return
        self._genotype_data_study_cache[study_id] = genotype_data_study
        self._genotype_data_study_wrapper_cache[study_id] = \
            StudyWrapper(genotype_data_study, self.pheno_db,
                         self.gene_weights_db)

    def _load_genotype_data_group_cache(self, genotype_data_group_ids=None):
        if genotype_data_group_ids is None:
            genotype_data_group_ids = set(self.get_genotype_data_groups_ids())

        assert isinstance(genotype_data_group_ids, set)

        cached_ids = set(self._genotype_data_group_cache.keys())
        if genotype_data_group_ids != cached_ids:
            to_load = genotype_data_group_ids - cached_ids
            for genotype_data_group_id in to_load:
                self._load_genotype_data_group_in_cache(genotype_data_group_id)

    def _load_genotype_data_group_in_cache(self, genotype_data_group_id):
        conf = self.genotype_data_group_configs.get(genotype_data_group_id)
        if not conf:
            return

        genotype_data_group = self.make_genotype_data_group(conf)
        if genotype_data_group is None:
            return
        self._genotype_data_group_cache[genotype_data_group_id] = \
            genotype_data_group
        self._genotype_data_group_wrapper_cache[genotype_data_group_id] = \
            StudyWrapper(genotype_data_group, self.pheno_db,
                         self.gene_weights_db)

    def make_genotype_data_study(self, study_config):
        if study_config is None:
            return None

        genotype_storage = self.genotype_storage_factory. \
            get_genotype_storage(study_config.genotype_storage.id)

        if genotype_storage is None:
            raise ValueError(
                "Unknown genotype storage: {}\nKnown ones: {}"
                .format(
                    study_config.genotype_storage,
                    self.genotype_storage_factory.get_genotype_storage_ids()
                )
            )

        variants = genotype_storage.build_backend(
            study_config, self.genomes_db
        )

        return GenotypeDataStudy(study_config, variants)

    def make_genotype_data_group(self, genotype_data_group_config):
        if genotype_data_group_config is None:
            return None

        genotype_studies = []
        for study_id in genotype_data_group_config.studies:
            genotype_data_study = self.get_study(study_id)

            if not genotype_data_study:
                raise ValueError(
                    "Unknown study: {}, known studies: [{}]".format(
                        genotype_data_group_config.studies,
                        ",".join(self.get_genotype_data_groups_ids())
                    ))
            genotype_studies.append(genotype_data_study)
        assert genotype_studies
        return GenotypeDataGroup(genotype_data_group_config, genotype_studies)
