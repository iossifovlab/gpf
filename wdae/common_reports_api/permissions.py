from django.core.cache import cache
import preloaded
from datasets_api.models import Dataset


def user_has_study_permission(user, study_name):
    study_name_to_dataset_id = cache.get('study_name_to_dataset_id')
    if study_name_to_dataset_id is None:
        print('Building cache...')
        studies = {
            ds.dataset_id: set(
                map(lambda d: d.name, ds.studies)
                + ds.descriptor['studies'].split(',')
            )
            for ds in user_has_study_permission.datasets_factory.get_datasets()
        }
        study_name_to_dataset_id = {
                study_name: dataset_id
                for dataset_id, study_names in studies.items()
                for study_name in study_names
            }

        cache.set('study_name_to_dataset_id', study_name_to_dataset_id, None)

    has_permission = False

    if study_name in study_name_to_dataset_id:
        ds_id = study_name_to_dataset_id[study_name]
        try:
            db_dataset = Dataset.objects.get(dataset_id=ds_id)
            if user.has_perm('datasets_api.view', db_dataset):
                has_permission = True
        except Dataset.DoesNotExist:
            raise

    return has_permission


user_has_study_permission.datasets = preloaded.register.get('datasets')
assert user_has_study_permission.datasets is not None

user_has_study_permission.datasets_factory = user_has_study_permission.datasets.get_factory()
