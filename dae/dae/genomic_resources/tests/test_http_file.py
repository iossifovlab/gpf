from dae.genomic_resources.http_file import HTTPFile


def test_ivan_explore_fixture_dir_name(fixture_dirname):
    dr = fixture_dirname("genomic_resources")
    assert dr
    print("DDDDDDDDDDDD: ", dr)


def test_http_file(resources_http_server):
    http_port = resources_http_server.http_port
    file_url = f"http://localhost:{http_port}/" \
        f"hg38/TESTCADD/genomic_resource.yaml"
    # file = HTTPFile(file_url)
    with HTTPFile(file_url) as file:
        print(file.read(100))
        print("====")
        print(file.read(100))
        print("====")
        print(file.read(100))
        print("====")
        print(file.read())


def test_http_genomic_sequence(resources_http_server):
    http_port = resources_http_server.http_port
    file_url = f"http://localhost:{http_port}/" \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/genome/chrAll.fa"

    with HTTPFile(file_url) as file:
        print(file.read(100))
        print("====")
        print(file.read(100))
        print("====")
        print(file.read(100))
        print("====")
