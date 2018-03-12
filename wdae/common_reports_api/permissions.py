# from django.core.cache import cache
import preloaded
from datasets_api.models import Dataset
from DAE import vDB
from collections import defaultdict
import itertools


def get_datasets_by_study(study_group_name):
    study_name_to_dataset_id = defaultdict(list)
    for ds in user_has_study_permission.datasets_factory.get_datasets():
        studies = [
            vDB.get_studies(study)
            for study in ds.descriptor['studies'].split(',')
        ]
        studies = itertools.chain(*studies)
        studies = [study.name for study in studies]
        for study in studies:
            study_name_to_dataset_id[study].append(ds.name)
        # studies[ds.dataset_id] = studies
    # study_name_to_dataset_id = {
    #         study_name: dataset_id
    #         for dataset_id, study_names in studies.items()
    #         for study_name in study_names
    #     }

    #     cache.set('study_name_to_dataset_id', study_name_to_dataset_id, None)

    studies = vDB.get_studies(study_group_name)
    ds_to_check = map(
        lambda s: study_name_to_dataset_id[s.name], studies)

    ds_to_check = map(frozenset, ds_to_check)
    return ds_to_check

def belongs_to_dataset(study_name):
    return len(list(itertools.chain(*get_datasets_by_study(study_name)))) != 0

def user_has_study_permission(user, study_group_name):
    ds_to_check = set(get_datasets_by_study(study_group_name))
    has_permission = all(
        any(
            user.has_perm('datasets_api.view', d)
            for d in itertools.imap(
                lambda d: Dataset.objects.get(dataset_id=d),
                datasets)
        )
        for datasets in ds_to_check
    )

    return has_permission


user_has_study_permission.datasets = preloaded.register.get('datasets')
assert user_has_study_permission.datasets is not None

user_has_study_permission.datasets_factory = \
    user_has_study_permission.datasets.get_factory()
