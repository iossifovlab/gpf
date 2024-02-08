import sys
import argparse
import logging
from typing import Optional

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae import __version__  # type: ignore
from dae.gpf_instance import GPFInstance


logger = logging.getLogger("gp_exporter")


def cli_export(
    argv: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None
) -> None:
    """CLI for exporting GP data."""
    if argv is None:
        argv = sys.argv[1:]

    desc = "Tool for export of Gene Profiles"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--version", action="store_true", default=False,
        help="Prints GPF version and exists.")
    VerbosityConfiguration.set_argumnets(parser)
    parser.add_argument(
        "--gpf", "-G", type=str, default=None,
        help="Path to GPF instance configuration file.")
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output file name to store exported data.")

    args = parser.parse_args(argv)

    if args.version:
        print(f"GPF version: {__version__}")
        sys.exit(0)

    VerbosityConfiguration.set(args)
    if gpf_instance is None:
        gpf_instance = GPFInstance.build(args.gpf)
    logger.info(
        "working with GPF instance from %s", gpf_instance.dae_dir)

    if not gpf_instance.get_gp_configuration():
        logger.warning("missing GP configuration; no GP to export")
        sys.exit(0)

    if args.output is None:
        outfile = sys.stdout
    else:
        # pylint: disable=consider-using-with
        outfile = open(args.output, "wt", encoding="utf8")

    try:
        rows = list(gpf_instance.query_gp_statistics(1))
        header = "\t".join(rows[0].keys())
        outfile.write(header)
        outfile.write("\n")

        page = 1
        while True:
            rows = list(gpf_instance.query_gp_statistics(page))
            if len(rows) == 0:
                break

            for row in rows:
                line = "\t".join(map(str, row.values()))
                outfile.write(line)
                outfile.write("\n")
            logger.debug("page %s exported", page)
            page += 1
    finally:
        if args.output is not None:
            outfile.close()
