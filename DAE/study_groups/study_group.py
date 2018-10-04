import itertools
import functools


class StudyGroup(object):

    def __init__(self, name, studies):
        self.studies = studies
        self.name = name
        self.phenotypes = functools.reduce(
            lambda acc, study: acc | study.phenotypes, studies, set())

        self._study_names = ",".join(study.name for study in self.studies)
        self._has_denovo = any([study.has_denovo for study in self.studies])
        self._has_transmitted =\
            any([study.has_transmitted for study in self.studies])
        self._has_complex = any([study.has_complex for study in self.studies])
        self._has_CNV = any([study.has_CNV for study in self.studies])
        study_types = set([study.study_type for study in self.studies
                           if study.study_type is not None])
        self._study_types = study_types if len(study_types) != 0 else None
        self._has_study_types = True if len(study_types) != 0 else False

    def get_variants(self, **kwargs):
        return itertools.chain(*[
            study.query_variants(**kwargs) for study in self.studies])

    def get_phenotype_values(self, pheno_column):
        result = set()
        for study in self.studies:
            result.update(study.get_phenotype_values(pheno_column))

        return result

    @property
    def study_names(self):
        return self._study_names

    @property
    def has_denovo(self):
        return self._has_denovo

    @property
    def has_transmitted(self):
        return self._has_transmitted

    @property
    def has_complex(self):
        return self._has_complex

    @property
    def has_CNV(self):
        return self._has_CNV

    @property
    def study_types(self):
        return self._study_types

    @property
    def has_study_types(self):
        return self._has_study_types
