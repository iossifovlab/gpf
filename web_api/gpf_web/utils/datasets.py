import json
from typing import Any


def find_dataset_id_in_dict(dictionary: dict) -> str | None:
    """Find dataset_id in a dictionary."""
    dataset_id = dictionary.get("dataset_id")
    if dataset_id is None:
        dataset_id = dictionary.get("datasetId")
    if dataset_id is None:
        dataset_id = dictionary.get("study_id")
    if dataset_id is None:
        dataset_id = dictionary.get("studyId")
    if dataset_id is None:
        dataset_id = dictionary.get("common_report_id")
    if dataset_id is None:
        dataset_id = dictionary.get("commonReportId")
    if dataset_id is None:
        query_data = dictionary.get("queryData")
        if query_data:
            if isinstance(query_data, str):
                query_data = json.loads(query_data)
            dataset_id = find_dataset_id_in_dict(query_data)
    return dataset_id


def find_dataset_id_in_request(request: Any) -> str | None:
    """Find dataset_id in a DRF request."""
    dataset_id = find_dataset_id_in_dict(request.query_params)
    if dataset_id is None:
        dataset_id = find_dataset_id_in_dict(request.data)
    if dataset_id is None:
        dataset_id = find_dataset_id_in_dict(request.resolver_match.kwargs)
    if dataset_id is None:
        dataset_id = request.parser_context.get("kwargs", {}).get(
            "common_report_id", None,
        )

    return dataset_id
