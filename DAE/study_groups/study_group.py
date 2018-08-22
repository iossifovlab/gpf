import itertools


class StudyGroup(object):

    def __init__(self, studies, name, phenotype=None):
        self.studies = studies
        self.name = name
        self.phenotype = phenotype

    def get_variants(self, **kwargs):
        return itertools.chain(*[
            study.query_variants(**kwargs) for study in self.studies])
