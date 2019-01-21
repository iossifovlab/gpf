from __future__ import print_function
from __future__ import unicode_literals

import itertools
import functools

from studies.study import StudyBase


class Dataset(StudyBase):

    def __init__(
            self, name, studies, dataset_config):
        super(Dataset, self).__init__(name, dataset_config)
        self.studies = studies

        self.dataset_config = dataset_config

        self.phenotypes = functools.reduce(
            lambda acc, study: acc | study.phenotypes, studies, set())

        self.study_names = ",".join(study.name for study in self.studies)
        self.has_denovo = any([study.has_denovo for study in self.studies])
        self.has_transmitted =\
            any([study.has_transmitted for study in self.studies])
        self.has_complex = any([study.has_complex for study in self.studies])
        self.has_cnv = any([study.has_cnv for study in self.studies])
        study_types = set([study.study_type for study in self.studies
                           if study.study_type is not None])
        self.study_types = study_types if len(study_types) != 0 else None
        self.study_type = ','.join(study_types) \
            if len(study_types) != 0 else None
        years = set([study.year for study in self.studies
                     if study.year is not None])
        self.years = years if len(years) != 0 else []
        self.year = ','.join(self.years)
        pub_meds = set([study.pub_med for study in self.studies
                        if study.pub_med is not None])
        self.pub_meds = pub_meds if len(pub_meds) != 0 else []
        self.pub_med = ','.join(self.pub_meds)
        
        self.has_study_types = True if len(study_types) != 0 else False

    # def get_variants(self, **kwargs):
    #     kwargs = self.transorm_variants_kwargs(**kwargs)

    #     return self.study_group.query_variants(**kwargs)

    # FIXME: fill these with real values
    def get_column_labels(self):
        return ['']

    def query_variants(self, **kwargs):
        return itertools.chain(*[
            study.query_variants(**kwargs) for study in self.studies])

    def get_phenotype_values(self, pheno_column='phenotype'):
        result = set()
        for study in self.studies:
            result.update(study.get_phenotype_values(pheno_column))

        return result

    def combine_families(self, first, second):
        same_families = set(first.keys()) & set(second.keys())
        combined_dict = {}
        combined_dict.update(first)
        combined_dict.update(second)
        for sf in same_families:
            combined_dict[sf] =\
                first[sf] if len(first[sf]) > len(second[sf]) else second[sf]
        return combined_dict

    # FIXME:
    def gene_sets_cache_file(self):
        cache_filename = '{}.json'.format(self.name)
        return cache_filename

        # study_groups_config = get_study_groups_config()
        # caches_dir = study_groups_config["DENOVO_GENE_SETS_DIR"]
        # cache_filename = '{}.json'.format(self.name)

        # return os.path.join(caches_dir, cache_filename)

    @property
    def families(self):
        return functools.reduce(lambda x, y: self.combine_families(x, y),
                                [study.families for study in self.studies])

    def _get_study_group_config_options(self, dataset_config):
        dataset_config['studyTypes'] = self.study_group.study_types
        dataset_config['genotypeBrowser']['hasStudyTypes'] =\
            self.study_group.has_study_types
        dataset_config['genotypeBrowser']['hasComplex'] =\
            self.study_group.has_complex
        dataset_config['genotypeBrowser']['hasCNV'] =\
            self.study_group.has_CNV
        dataset_config['genotypeBrowser']['hasDenovo'] =\
            self.study_group.has_denovo
        dataset_config['genotypeBrowser']['hasTransmitted'] =\
            self.study_group.has_transmitted
        dataset_config['studies'] =\
            self.study_group.study_names

        return dataset_config

    def get_dataset_description(self):
        keys = Dataset._get_dataset_description_keys()
        dataset_config = self.dataset_config.to_dict()

        dataset_config = self._get_study_group_config_options(dataset_config)

        return {key: dataset_config[key] for key in keys}
