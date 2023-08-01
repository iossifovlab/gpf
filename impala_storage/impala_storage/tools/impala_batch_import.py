#!/usr/bin/env python

import sys
import logging
from typing import Optional

from impala_storage.schema1.import_commons import BatchImporter

logger = logging.getLogger(__name__)


def main(argv: Optional[list[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    BatchImporter.main(argv)


if __name__ == "__main__":

    main()
