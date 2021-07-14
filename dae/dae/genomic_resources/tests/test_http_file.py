from dae.genomic_resources.http_file import HTTPFile


def test_cache_http(resources_http_server):
    file_url = "http://localhost:16200/hg38/TESTCADD/genomic_resource.yaml"
    file = HTTPFile(file_url)
    print(file.read(100))
    print("====")
    print(file.read(100))
    print("====")
    print(file.read(100))
    print("====")
    print(file.read())
