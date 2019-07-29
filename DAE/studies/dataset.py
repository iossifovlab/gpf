import itertools
import functools

from studies.study import StudyBase


class Dataset(StudyBase):

    def __init__(self, dataset_config, studies):
        super(Dataset, self).__init__(dataset_config)
        self.studies = studies
        self.study_names = ",".join(study.name for study in self.studies)

    def query_variants(self, **kwargs):
        return itertools.chain(*[
                study.query_variants(**kwargs) for study in self.studies])

    @property
    def families(self):
        return functools.reduce(
            lambda x, y: self._combine_families(x, y),
            [study.families for study in self.studies])

    def _combine_families(self, first, second):
        same_families = set(first.keys()) & set(second.keys())
        combined_dict = {}
        combined_dict.update(first)
        combined_dict.update(second)
        for sf in same_families:
            combined_dict[sf] =\
                first[sf] if len(first[sf]) > len(second[sf]) else second[sf]
        return combined_dict

    def get_pedigree_values(self, column):
        return functools.reduce(
            lambda x, y: x | y,
            [st.get_pedigree_values(column) for st in self.studies], set())

    def get_people_with_people_group(self, people_group, people_group_value):
        return functools.reduce(
            lambda x, y: x | y,
            [st.get_people_with_people_group(people_group, people_group_value)
             for st in self.studies], set())
