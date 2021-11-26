import gzip
import os


def handle_chrom_prefix(expect_prefix, data):
    if data is None:
        return data
    if expect_prefix and not data.startswith("chr"):
        return "chr{}".format(data)
    if not expect_prefix and data.startswith("chr"):
        return data[3:]
    return data


def is_gzip(filename):
    try:
        if filename == "-" or not os.path.exists(filename):
            return False
        with gzip.open(filename, "rt") as infile:
            infile.readline()
        return True
    except Exception:
        return False


def regions_intersect(b1: int, e1: int, b2: int, e2: int) -> bool:
    assert b1 <= e1 and b2 <= e2
    return b2 <= e1 and b1 <= e2
