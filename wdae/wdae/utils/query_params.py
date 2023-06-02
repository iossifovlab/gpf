import json


def parse_query_params(data):
    res = {str(k): str(v) for k, v in list(data.items())}
    return json.loads(res["queryData"])
