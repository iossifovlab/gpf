#!/usr/bin/env python

import sys

from dae.backends.impala.import_commons import MakefileGenerator


def main(argv=sys.argv[1:]):
    MakefileGenerator.main(argv=sys.argv[1:])


if __name__ == "__main__":
    main()
