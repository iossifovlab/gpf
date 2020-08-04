#!/usr/bin/env python

import sys

from dae.backends.impala.import_commons import BatchImporter


def main(argv=sys.argv[1:]):
    BatchImporter.main(argv=sys.argv[1:])


if __name__ == "__main__":
    main()
