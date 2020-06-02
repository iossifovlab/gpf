import logging
from threading import Lock

from django.conf import settings

from dae.gpf_instance.gpf_instance import GPFInstance


logger = logging.getLogger(__name__)
__all__ = ["get_gpf_instance"]


_gpf_instance = None
_gpf_recreated_dataset_perm = False
_gpf_instance_lock = Lock()


def get_gpf_instance():
    load_gpf_instance()
    _recreated_dataset_perm()

    return _gpf_instance


def load_gpf_instance():
    logger.warn("CALLED: load_gpf_instance() ...")

    global _gpf_instance
    global _gpf_instance_lock

    if _gpf_instance is None:
        _gpf_instance_lock.acquire()
        try:
            if _gpf_instance is None:
                gpf_instance = GPFInstance(load_eagerly=True)
                _gpf_instance = gpf_instance
        finally:
            _gpf_instance_lock.release()

    logger.warn("DONE: load_gpf_instance() ...")
    return _gpf_instance


def _recreated_dataset_perm():
    global _gpf_instance
    global _gpf_instance_lock
    global _gpf_recreated_dataset_perm

    if _gpf_recreated_dataset_perm:
        return

    _gpf_instance_lock.acquire()
    try:
        assert _gpf_instance is not None

        if not _gpf_recreated_dataset_perm:
            from datasets_api.models import Dataset
            for study_id in _gpf_instance.get_genotype_data_ids():
                Dataset.recreate_dataset_perm(study_id, [])
            _gpf_recreated_dataset_perm = True
    finally:
        _gpf_instance_lock.release()
