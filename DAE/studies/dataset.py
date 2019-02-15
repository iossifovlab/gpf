from __future__ import print_function
from __future__ import unicode_literals

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

    # FIXME:
    def gene_sets_cache_file(self):
        cache_filename = '{}.json'.format(self.name)
        return cache_filename

        # study_groups_config = get_study_groups_config()
        # caches_dir = study_groups_config["DENOVO_GENE_SETS_DIR"]
        # cache_filename = '{}.json'.format(self.name)

        # return os.path.join(caches_dir, cache_filename)

    # FIXME: fill these with real values
    def get_column_labels(self):
        return ['']
