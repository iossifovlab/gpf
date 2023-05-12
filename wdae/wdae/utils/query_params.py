import json


def parse_query_params(data):
    res = {str(k): str(v) for k, v in list(data.items())}
    assert "queryData" in res
    query = json.loads(res["queryData"])
    return query
