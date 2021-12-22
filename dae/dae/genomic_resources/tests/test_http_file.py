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
        "hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa"

    with HTTPFile(file_url) as file:
        print(file.read(100))
        print("====")
        print(file.read(100))
        print("====")
        print(file.read(100))
        print("====")


def test_load_gzip_file():
    import gzip
    htf = HTTPFile("https://www.iossifovlab.com/distribution/public/genomic-resources-repository/hg38/GRCh38-hg38/gene_models/refSeq_v20200330/refSeq_20200330.txt.gz")
    ss = gzip.open(htf, "rt")
    h = ss.readline()
    for line in ss:
        assert line[-2] == ','


def test_load_text_file():
    htf = HTTPFile("https://www.iossifovlab.com/distribution/public/genomic-resources-repository/hg38/GRCh38-hg38/gene_models/refSeq_v20200330/genomic_resource.yaml",
                   buffer_size=2)

    s = ''
    while True:
        bb = htf.read(2)
        if not bb:
            break
        bbs = bb.decode()
        s += str(bbs)
        print("IIII BBBBBBB", bbs)
    print("IIII   SSSSSS", s)


def test_time_download_speed():
    import time
    from urllib.request import urlopen
    url = "https://www.iossifovlab.com/distribution/public/genomic-resources-repository/hg38/GRCh38-hg38/gene_models/refSeq_v20200330/refSeq_20200330.txt.gz"

    tb = time.time()
    uuu = urlopen(url)
    length = 0
    while bf := uuu.read(1024*8):
        length += len(bf)
    uuu.close()
    te = time.time()
    print(f"UUUUUU ulropen loaded {length} bytes in {te-tb} seconds")

    tb = time.time()
    htf = HTTPFile(url)
    length = 0
    while bf := htf.read(1024*8):
        length += len(bf)
    htf.close()
    te = time.time()
    print(f"UUUUUU HTTPFile loaded {length} bytes in {te-tb} seconds")
