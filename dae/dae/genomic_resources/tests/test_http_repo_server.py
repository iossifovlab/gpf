from urllib.request import urlopen


def test_http_repo_server(resources_http_server):
    http_port = resources_http_server.http_port

    print(resources_http_server.http_port)
    print(resources_http_server.directory)

    url = f"http://localhost:{http_port}/"

    with urlopen(url) as infile:
        while data := infile.read():
            print(data)
