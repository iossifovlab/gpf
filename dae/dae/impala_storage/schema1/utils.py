import re


def generate_file_access_glob(partition_descriptor):
    """Return a glob for accessing every parquet file in the partition."""
    partition = partition_descriptor.dataset_family_partition()
    glob_parts = ["*" for _ in partition]
    glob_parts.append("*.parquet")
    return "/".join(glob_parts)


def variants_filename_basedir(partition_descriptor, filename):
    """Extract the variants basedir from filename."""
    partition = partition_descriptor.dataset_family_partition()
    regex_parts = [
        "^(?P<basedir>.+)",
        *[f"({bname}=.+)" for (bname, _) in partition],
        "(?P<filename>.+).parquet$"
    ]
    regexp = re.compile("/".join(regex_parts))
    match = regexp.match(filename)
    if not match:
        return None

    assert "basedir" in match.groupdict()
    basedir = match.groupdict()["basedir"]
    if basedir and basedir[-1] != "/":
        basedir += "/"
    return basedir