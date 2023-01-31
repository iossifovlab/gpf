from functools import wraps
from utils.datasets import find_dataset_id_in_request


def inject_dataset(func):
    """Inject a dataset property into the request of a view method."""

    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        dataset_id = find_dataset_id_in_request(request)
        dataset = self.variants_db.get_wdae_wrapper(dataset_id)

        request.dataset = dataset
        return func(self, request, *args, **kwargs)

    return wrapper
