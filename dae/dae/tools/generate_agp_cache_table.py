#!/usr/bin/env python
import os
import time
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance

logger = logging.getLogger(__name__)


def main(gpf_instance=None, argv=None):
    description = "Generate autism gene profiles cache tool"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--verbose", "-V", "-v", action="count", default=0)
    default_dbfile = os.path.join(os.getenv("DAE_DB_DIR", "./"), "agpdb")
    parser.add_argument("--dbfile", default=default_dbfile)
    parser.add_argument("--drop", action="store_true")

    args = parser.parse_args(argv)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    start = time.time()
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    agpdb = gpf_instance._autism_gene_profile_db

    if args.drop:
        agpdb.drop_cache_table()
    else:
        if agpdb.cache_table_exists():
            agpdb.generate_cache_table(regenerate=True)
        else:
            agpdb.generate_cache_table(regenerate=False)

    duration = time.time() - start

    logger.info(duration)
    logger.info("Done")


if __name__ == "__main__":
    main()
