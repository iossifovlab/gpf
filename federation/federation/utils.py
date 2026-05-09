from rest_client.rest_client import RESTClient


def prefix_remote_identifier(string: str, rest_client: RESTClient) -> str:
    return f"{rest_client.client_id}_{string}"


def prefix_remote_name(string: str, rest_client: RESTClient) -> str:
    return f"({rest_client.client_id}) {string}"
