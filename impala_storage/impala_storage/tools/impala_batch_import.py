#!/usr/bin/env python

import logging
import sys

from impala_storage.schema1.import_commons import BatchImporter

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    BatchImporter.main(argv)


if __name__ == "__main__":

    main()
