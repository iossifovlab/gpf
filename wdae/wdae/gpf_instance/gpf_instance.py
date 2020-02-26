from threading import Lock

from dae.gpf_instance.gpf_instance import GPFInstance

from datasets_api.models import Dataset


__all__ = ["get_gpf_instance"]


_gpf_instance = None
_gpf_instance_lock = Lock()


def get_gpf_instance():
    global _gpf_instance
    global _gpf_instance_lock

    if _gpf_instance is None:
        _gpf_instance_lock.acquire()
        try:
            if _gpf_instance is None:
                gpf_instance = GPFInstance(load_eagerly=True)
                reload_datasets(gpf_instance._variants_db)
                _gpf_instance = gpf_instance
        finally:
            _gpf_instance_lock.release()

    return _gpf_instance


def reload_datasets(variants_db):
    for study_id in variants_db.get_all_ids():
        Dataset.recreate_dataset_perm(study_id, [])
