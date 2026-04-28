import json
from typing import cast


def parse_query_params(data: dict) -> dict:
    res = {str(k): str(v) for k, v in list(data.items())}
    return cast(dict, json.loads(res["queryData"]))
