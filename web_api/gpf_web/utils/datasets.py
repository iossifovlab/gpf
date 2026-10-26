import json
from collections.abc import Mapping
from typing import Any

DATASET_ID_KEYS = (
    "dataset_id",
    "datasetId",
    "study_id",
    "studyId",
    "common_report_id",
    "commonReportId",
)


class ConflictingDatasetIdsError(ValueError):
    """A request names more than one dataset id."""

    def __init__(self, dataset_ids: set[str]) -> None:
        super().__init__(
            f"request names conflicting dataset ids: {sorted(dataset_ids)}",
        )
        self.dataset_ids = dataset_ids


def find_dataset_ids_in_dict(dictionary: Any) -> set[str]:
    """Collect the dataset ids under every key that names a dataset."""
    if not isinstance(dictionary, Mapping):
        return set()
    dataset_ids = {
        str(dictionary[key]) for key in DATASET_ID_KEYS
        if dictionary.get(key) is not None
    }
    query_data = dictionary.get("queryData")
    if query_data:
        if isinstance(query_data, str):
            query_data = json.loads(query_data)
        dataset_ids |= find_dataset_ids_in_dict(query_data)
    return dataset_ids


def find_dataset_ids_in_request(request: Any) -> set[str]:
    """Collect the dataset ids from the URL, the query and the body."""
    dataset_ids = find_dataset_ids_in_dict(request.query_params)
    dataset_ids |= find_dataset_ids_in_dict(request.data)
    dataset_ids |= find_dataset_ids_in_dict(request.resolver_match.kwargs)
    dataset_ids |= find_dataset_ids_in_dict(
        request.parser_context.get("kwargs", {}),
    )
    return dataset_ids


def find_dataset_id_in_request(request: Any) -> str | None:
    """Find the dataset id of a DRF request.

    The URL kwargs, the query parameters and the body can each name a
    dataset. Return ``None`` when none of them does. Raise
    ``ConflictingDatasetIdsError`` when they name different datasets.
    """
    dataset_ids = find_dataset_ids_in_request(request)
    if len(dataset_ids) > 1:
        raise ConflictingDatasetIdsError(dataset_ids)
    if not dataset_ids:
        return None
    return dataset_ids.pop()
