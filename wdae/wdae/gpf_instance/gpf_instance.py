import logging
from django.conf import settings

from threading import Lock

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.remote.remote_study_wrapper import RemoteStudyWrapper
from dae.remote.rest_api_client import RESTClient

from requests.exceptions import ConnectionError


logger = logging.getLogger(__name__)
__all__ = ["get_gpf_instance"]


_gpf_instance = None
_gpf_recreated_dataset_perm = False
_gpf_instance_lock = Lock()


class WGPFInstance(GPFInstance):
    def __init__(self, *args, **kwargs):
        super(WGPFInstance, self).__init__(*args, **kwargs)
        self._remote_study_clients = dict()
        self._remote_study_wrappers = dict()

        if settings.REMOTES:
            for remote in settings.REMOTES:
                print("Creating remote")
                print(remote)
                try:
                    client = RESTClient(
                        remote["id"],
                        remote["host"],
                        remote["user"],
                        remote["password"],
                        base_url=remote["base_url"],
                        port=remote["port"],

                    )
                    self._fetch_remote_studies(client)
                except ConnectionError:
                    print(f"Failed to create remote {remote['id']}")

    def _fetch_remote_studies(self, rest_client):
        studies = rest_client.get_datasets()
        for study in studies["data"]:
            study_wrapper = RemoteStudyWrapper(study["id"], rest_client)
            study_id = study_wrapper.study_id
            self._remote_study_clients[study_id] = rest_client
            self._remote_study_wrappers[study_id] = study_wrapper

    def get_wdae_wrapper(self, dataset_id):
        wrapper = super(WGPFInstance, self).get_wdae_wrapper(dataset_id)
        if not wrapper:
            wrapper = self._remote_study_wrappers.get(dataset_id, None)
        return wrapper

    def get_genotype_data_ids(self):
        return (
            list(super(WGPFInstance, self).get_genotype_data_ids())
            + self.remote_studies
        )

    def get_genotype_data(self, dataset_id):
        pass

    @property
    def remote_studies(self):
        return list(self._remote_study_clients.keys())


def get_gpf_instance():
    load_gpf_instance()
    _recreated_dataset_perm()

    return _gpf_instance


def load_gpf_instance():

    global _gpf_instance
    global _gpf_instance_lock

    if _gpf_instance is None:
        _gpf_instance_lock.acquire()
        try:
            if _gpf_instance is None:
                gpf_instance = WGPFInstance(load_eagerly=True)
                _gpf_instance = gpf_instance
        finally:
            _gpf_instance_lock.release()

    return _gpf_instance


def reload_datasets(gpf_instance):
    from datasets_api.models import Dataset
    for study_id in gpf_instance.get_genotype_data_ids():
        Dataset.recreate_dataset_perm(study_id, [])


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
            reload_datasets(_gpf_instance)
            _gpf_recreated_dataset_perm = True
    finally:
        _gpf_instance_lock.release()
