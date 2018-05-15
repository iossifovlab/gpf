from builtins import next
import heapq
import itertools

from datasets.dataset import Dataset
from functools import reduce

class MetaDataset(Dataset):

    ID = 'META'

    def __init__(self, meta_dataset_descriptor, datasets):
        super(MetaDataset, self).__init__(meta_dataset_descriptor)
        self.datasets = datasets

    @staticmethod
    def __distinct(variants, max_count=None):
        count = 0
        previous_variant = next(variants)
        seen_keys = {previous_variant.key}
        for variant in variants:
            if previous_variant == variant:
                if previous_variant.studyName != variant.studyName:
                    previous_variant.studyName += "; " + variant.studyName
            else:
                if variant.key not in seen_keys:
                    yield previous_variant
                    previous_variant = variant
                    seen_keys.add(variant.key)
                    if max_count and ++count >= max_count:
                        return
        yield previous_variant

    def get_variants(self, safe=True, **kwargs):
        dataset_ids = kwargs['dataset_ids']
        studies = []
        studies_datasets = {}
        for dataset in filter(
                lambda ds: ds.dataset_id in dataset_ids,
                self.datasets):
            for study in dataset.get_studies(safe=safe, **kwargs):
                if study.name not in studies_datasets:
                    studies_datasets[study.name] = []
                studies_datasets[study.name].append(dataset.name)
                studies.append(study)

        studies = sorted(studies, key=lambda st: st.name)
        unique_studies = []
        for study in studies:
            if len(unique_studies) == 0 or unique_studies[-1].name != study.name:
                study.dataset_name = reduce(
                    lambda x, y: '{}; {}'.format(x, y),
                    studies_datasets[study.name])
                unique_studies.append(study)

        all_variants = heapq.merge(
                *[self.__get_variants_from_study(study, safe=safe, **kwargs)
                 for study in unique_studies])

        augment_vars = self._get_var_augmenter(safe=safe, **kwargs)
        return map(
            augment_vars,
            self.__distinct(self._phenotype_filter(all_variants, **kwargs))
        )

    def __get_variants_from_study(self, study, safe=True, **kwargs):
        variant_iterators = []
        if study.has_denovo:
            denovo_filters = self.get_denovo_filters(safe=safe, **kwargs)
            variant_iterators.append(study.get_denovo_variants(**denovo_filters))

        if study.has_transmitted:
            transmitted_filters = self.get_transmitted_filters(safe=safe, **kwargs)
            present_in_parent = transmitted_filters.get('presentInParent')
            if transmitted_filters.get('familyIds', None) != [] and \
                    not (present_in_parent and present_in_parent == ['neither']):
                variant_iterators.append(study.get_transmitted_variants(**transmitted_filters))

        for variant in heapq.merge(*variant_iterators):
            variant.atts['dataset'] = study.dataset_name
            yield variant
