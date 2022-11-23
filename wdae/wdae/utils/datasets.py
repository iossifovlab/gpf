import json

def find_dataset_id_in_dict(dictionary):
    dataset_id = dictionary.get("dataset_id", None)
    if dataset_id is None:
        dataset_id = dictionary.get("datasetId", None)
    if dataset_id is None:
        dataset_id = dictionary.get("study_id", None)
    if dataset_id is None:
        dataset_id = dictionary.get("studyId", None)
    if dataset_id is None:
        dataset_id = dictionary.get("common_report_id", None)
    if dataset_id is None:
        dataset_id = dictionary.get("commonReportId", None)
    if dataset_id is None:
        query_data = dictionary.get("queryData", None)
        if query_data:
            if isinstance(query_data, str):
                query_data = json.loads(query_data)
            dataset_id = find_dataset_id_in_dict(query_data)
    return dataset_id

def find_dataset_id_in_request(request):
    dataset_id = find_dataset_id_in_dict(request.query_params)
    if dataset_id is None:
        dataset_id = find_dataset_id_in_dict(request.data)
    if dataset_id is None:
        dataset_id = find_dataset_id_in_dict(request.resolver_match.kwargs)
    if dataset_id is None:
        dataset_id = request.parser_context.get("kwargs", {}).get(
            "common_report_id", None
        )

    return dataset_id
