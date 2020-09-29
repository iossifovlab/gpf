#!/usr/bin/env python

import sys
import logging

logger = logging.getLogger(__name__)


from dae.backends.impala.import_commons import BatchImporter


def main(argv=sys.argv[1:]):
    BatchImporter.main(argv=sys.argv[1:])


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.info('Started')

    main()

    logger.info('Done')
