from utils.datasets import find_dataset_id_in_request


def inject_dataset(func):
    """Injects a dataset property into the request of a view method"""
    def wrapper(self, request, dataset, *args, **kwargs):
        dataset_id = find_dataset_id_in_request()
        if dataset_id is None:
            dataset = None
        else:
            dataset = self.variants_db.get_wdae_wrapper(dataset_id)

        return func(self, request, dataset, *args, **kwargs)
