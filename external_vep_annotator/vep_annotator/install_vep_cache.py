import argparse
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    """VEP cache installation tool"""
    parser = argparse.ArgumentParser(
        description="VEP cache installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "cache_dir",
        help="Destination directory to download and unpack the cache in",
    )
    parser.add_argument(
        "--force", "-f", default=False, action="store_true",
        help="Download and unpack regardless of destination status",
    )
    parser.add_argument(
        "--continue", "-c", dest="cont", default=False, action="store_true",
        help="Continue a previous partial download",
    )

    args = parser.parse_args(argv)

    cache_dir = Path(args.cache_dir).absolute()

    force = args.force
    cont = args.cont

    filename = "homo_sapiens_vep_113_GRCh38.tar.gz"
    filepath = cache_dir / filename

    if cont:
        other_files = list(filter(
            lambda file: file.name != filename, cache_dir.iterdir(),
        ))
    else:
        other_files = list(cache_dir.iterdir())

    if cache_dir.exists() and len(other_files) > 0 and not force:
        raise ValueError(
            "Destination cache directory is not empty! "
            "Use --force or cleanup the directory.",
        )

    file_url = (
        "https://ftp.ensembl.org/"
        "pub/release-113/variation/vep/"
        "homo_sapiens_vep_113_GRCh38.tar.gz"
    )

    wget_command = [
        "wget",
        file_url,
        "-O",
        str(filepath),
    ]
    if cont:
        wget_command.append("-c")
    try:
        subprocess.run(wget_command, check=True)
    except subprocess.CalledProcessError:
        logger.exception("Error downloading cache")
        return 1

    tar_command = [
        "tar",
        "xzf",
        str(filepath),
        "-C",
        str(cache_dir),
    ]

    try:
        subprocess.run(tar_command, check=True)
    except subprocess.CalledProcessError:
        logger.exception("Error extracting cache")
        return 2

    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
