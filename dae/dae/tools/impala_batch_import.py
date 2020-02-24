#!/usr/bin/env python

import sys

from dae.backends.impala.import_commons import MakefileGenerator


if __name__ == "__main__":

    MakefileGenerator.main(argv=sys.argv[1:])
