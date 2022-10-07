#!/usr/bin/env python

import sys
import logging

from dae.impala_storage.schema1.import_commons import BatchImporter

logger = logging.getLogger(__name__)


def main(argv=sys.argv[1:]):
    BatchImporter.main(argv=sys.argv[1:])


if __name__ == "__main__":

    main()
