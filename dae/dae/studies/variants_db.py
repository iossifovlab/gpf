from dae.studies.study import Study
from dae.studies.dataset import Dataset
from dae.studies.study_wrapper import StudyWrapper
from dae.studies.study_config_parser import StudyConfigParser
from dae.studies.dataset_config_parser import DatasetConfigParser


class VariantsDb(object):

    def __init__(
            self, dae_config, pheno_factory, gene_weights_db, genomes_db,
            genotype_storage_factory):
        self.dae_config = dae_config

        assert pheno_factory is not None
        assert gene_weights_db is not None
        assert genomes_db is not None
        assert genotype_storage_factory is not None

        self.pheno_factory = pheno_factory
        self.gene_weights_db = gene_weights_db
        self.genomes_db = genomes_db
        self.genotype_storage_factory = genotype_storage_factory

        defaults = {
            'values': {
                'dae_data_dir': self.dae_config.dae_data_dir
            }
        }
        if dae_config.default_configuration and \
                dae_config.default_configuration.conf_file:
            defaults['conf'] = dae_config.default_configuration.conf_file

        self.study_configs = \
            StudyConfigParser.read_and_parse_directory_configurations(
                dae_config.studies_db.dir,
                defaults=defaults
            )

        self.dataset_configs = \
            DatasetConfigParser.read_and_parse_directory_configurations(
                dae_config.datasets_db.dir,
                self.study_configs,
                defaults=defaults,
                fail_silently=True
            )

        self._study_cache = {}
        self._study_wrapper_cache = {}

        self._dataset_cache = {}
        self._dataset_wrapper_cache = {}

        self._configuration_check()

    def _configuration_check(self):
        studies_ids = set(self.get_studies_ids())
        dataset_ids = set(self.get_datasets_ids())

        overlapping = studies_ids.intersection(dataset_ids)

        assert overlapping == set(), \
            "Overlapping studies and datasets ids: {}".format(overlapping)

    def get_studies_ids(self):
        return list(self.study_configs.keys())

    def get_study_config(self, study_id):
        self.load_study_cache({study_id})
        if study_id not in self._study_cache:
            return None

        return self._study_cache.get(study_id).config

    def get_study(self, study_id):
        self.load_study_cache({study_id})
        if study_id not in self._study_cache:
            return None

        return self._study_cache[study_id]

    def get_study_wdae_wrapper(self, study_id):
        self.load_study_cache({study_id})

        if study_id not in self._study_wrapper_cache:
            return None

        return self._study_wrapper_cache[study_id]

    def get_all_studies(self):
        self.load_study_cache()

        return list(self._study_cache.values())

    def get_all_studies_wrapper(self):
        self.load_study_cache()

        return list(self._study_wrapper_cache.values())

    def get_all_study_configs(self):
        self.load_study_cache()

        return [study.config for study in self._study_cache.values()]

    def get_datasets_ids(self):
        return list(self.dataset_configs.keys())

    def get_dataset_config(self, dataset_id):
        self.load_dataset_cache({dataset_id})
        if dataset_id not in self._dataset_cache:
            return None

        return self._dataset_cache.get(dataset_id).config

    def get_dataset(self, dataset_id):
        self.load_dataset_cache({dataset_id})

        if dataset_id not in self._dataset_cache:
            return None

        return self._dataset_cache[dataset_id]

    def get_dataset_wdae_wrapper(self, dataset_id):
        self.load_dataset_cache({dataset_id})

        if dataset_id not in self._dataset_wrapper_cache:
            return None

        return self._dataset_wrapper_cache[dataset_id]

    def get_all_datasets(self):
        self.load_dataset_cache()

        return list(self._dataset_cache.values())

    def get_all_datasets_wrapper(self):
        self.load_dataset_cache()

        return list(self._dataset_wrapper_cache.values())

    def get_all_dataset_configs(self):
        self.load_dataset_cache()

        return [dataset.config for dataset in self._dataset_cache.values()]

    def get_all_ids(self):
        return self.get_studies_ids() + self.get_datasets_ids()

    def get_config(self, config_id):
        study_config = self.get_study_config(config_id)
        dataset_config = self.get_dataset_config(config_id)
        return study_config if study_config else dataset_config

    def get(self, object_id):
        study = self.get_study(object_id)
        dataset = self.get_dataset(object_id)
        return study if study else dataset

    def get_wdae_wrapper(self, wdae_wrapper_id):
        study_wdae_wrapper = self.get_study_wdae_wrapper(wdae_wrapper_id)
        dataset_wdae_wrapper = self.get_dataset_wdae_wrapper(wdae_wrapper_id)
        return study_wdae_wrapper\
            if study_wdae_wrapper else dataset_wdae_wrapper

    def get_all_configs(self):
        study_configs = self.get_all_study_configs()
        dataset_configs = self.get_all_dataset_configs()
        return study_configs + dataset_configs

    def get_all(self):
        studies = self.get_all_studies()
        datasets = self.get_all_datasets()
        return studies + datasets

    def get_all_wrappers(self):
        study_wrappers = self.get_all_studies_wrapper()
        dataset_wrappers = self.get_all_datasets_wrapper()
        return study_wrappers + dataset_wrappers

    def load_study_cache(self, study_ids=None):
        if study_ids is None:
            study_ids = set(self.get_studies_ids())

        assert isinstance(study_ids, set)

        cached_ids = set(self._study_cache.keys())
        if study_ids != cached_ids:
            to_load = study_ids - cached_ids
            for study_id in to_load:
                self._load_study_in_cache(study_id)

    def wrap_study(self, study):
        return StudyWrapper(study, self.pheno_factory, self.gene_weights_db)

    def _load_study_in_cache(self, study_id):
        conf = self.study_configs.get(study_id)
        if not conf:
            return

        study = self.make_study(conf)
        if study is None:
            return
        self._study_cache[study_id] = study
        self._study_wrapper_cache[study_id] = \
            StudyWrapper(study, self.pheno_factory, self.gene_weights_db)

    def load_dataset_cache(self, dataset_ids=None):
        if dataset_ids is None:
            dataset_ids = set(self.get_datasets_ids())

        assert isinstance(dataset_ids, set)

        cached_ids = set(self._dataset_cache.keys())
        if dataset_ids != cached_ids:
            to_load = dataset_ids - cached_ids
            for dataset_id in to_load:
                self._load_dataset_in_cache(dataset_id)

    def _load_dataset_in_cache(self, dataset_id):
        conf = self.dataset_configs.get(dataset_id)
        if not conf:
            return

        dataset = self.make_dataset(conf)
        if dataset is None:
            return
        self._dataset_cache[dataset_id] = dataset
        self._dataset_wrapper_cache[dataset_id] = \
            StudyWrapper(dataset, self.pheno_factory, self.gene_weights_db)

    def make_study(self, study_config):
        if study_config is None:
            return None

        genotype_storage = self.genotype_storage_factory. \
            get_genotype_storage(study_config.genotype_storage)

        if genotype_storage is None:
            raise ValueError(
                "Unknown genotype storage: {}\nKnown ones: {}"
                .format(
                    study_config.genotype_storage,
                    self.genotype_storage_factory.get_genotype_storage_ids()
                )
            )

        variants = genotype_storage.get_backend(
            study_config.id, self.genomes_db
        )

        return Study(study_config, variants)

    def make_dataset(self, dataset_config):
        if dataset_config is None:
            return None

        studies = []
        for study_id in dataset_config.studies:
            study = self.get_study(study_id)

            if not study:
                raise ValueError(
                    "Unknown study: {}, known studies: [{}]".format(
                        dataset_config.studies,
                        ",".join(self.get_datasets_ids())
                    ))
            studies.append(study)
        assert studies

        return Dataset(dataset_config, studies)
