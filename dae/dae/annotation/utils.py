import gzip
import os


def handle_chrom_prefix(expect_prefix, data):
    """Add or delete the chromosome prefix."""
    if data is None:
        return data
    if expect_prefix and not data.startswith("chr"):
        return f"chr{data}"
    if not expect_prefix and data.startswith("chr"):
        return data[3:]
    return data


def is_gzip(filename):
    """Check if a file is gzipped."""
    try:
        if filename == "-" or not os.path.exists(filename):
            return False
        with gzip.open(filename, "rt") as infile:
            infile.readline()
        return True
    except Exception:  # pylint: disable=broad-except
        return False


def regions_intersect(beg1: int, end1: int, beg2: int, end2: int) -> bool:
    assert beg1 <= end1 and beg2 <= end2
    return beg2 <= end1 and beg1 <= end2
