import itertools
import functools


class StudyGroup(object):

    def __init__(self, name, studies):
        self.studies = studies
        self.name = name
        self.phenotypes = functools.reduce(
            lambda acc, study: acc | study.phenotypes, studies, set())

    def get_variants(self, **kwargs):
        return itertools.chain(*[
            study.query_variants(**kwargs) for study in self.studies])

    @property
    def study_names(self):
        return ",".join(study.name for study in self.studies)
