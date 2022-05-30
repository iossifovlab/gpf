def find_dataset_id_in_request(request):
    dataset_id = request.query_params.get("dataset_id", None)
    if dataset_id is None:
        dataset_id = request.query_params.get("datasetId", None)
    if dataset_id is None:
        dataset_id = request.data.get("datasetId", None)
    if dataset_id is None:
        dataset_id = request.data.get("dataset_id", None)
    if dataset_id is None:
        dataset_id = request.parser_context.get("kwargs", {}).get(
            "common_report_id", None
        )

    return dataset_id
