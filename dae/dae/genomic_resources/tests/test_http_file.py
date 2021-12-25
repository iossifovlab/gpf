import fsspec
import pytest


DEFAULT_URL = "https://www.iossifovlab.com/distribution/" \
    "public/genomic-resources-repository"


@pytest.mark.internet
def test_load_gzip_file_fsspec():
    import gzip
    with fsspec.open(
            f"{DEFAULT_URL}/hg38/gene_models/refSeq_v20200330/"
            f"refSeq_20200330.txt.gz") as htf:

        with gzip.open(htf, "rt") as ss:
            ss.readline()

            for line in ss:
                assert line[-2] == ','


@pytest.mark.internet
def test_time_download_speed():
    import time
    from urllib.request import urlopen
    url = f"{DEFAULT_URL}/hg38/gene_models/refSeq_v20200330/" \
        f"refSeq_20200330.txt.gz"

    tb = time.time()
    uuu = urlopen(url)
    length = 0
    while bf := uuu.read(1024*8):
        length += len(bf)
    uuu.close()
    te = time.time()
    print(f"UUUUUU ulropen loaded {length} bytes in {te-tb} seconds")

    tb = time.time()
    with fsspec.open(
            f"{DEFAULT_URL}/hg38/gene_models/refSeq_v20200330/"
            f"refSeq_20200330.txt.gz") as htf:

        length = 0
        while bf := htf.read(1024*8):
            length += len(bf)
        te = time.time()
        print(f"UUUUUU fsspec loaded {length} bytes in {te-tb} seconds")
