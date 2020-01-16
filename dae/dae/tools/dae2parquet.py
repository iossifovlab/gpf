#!/usr/bin/env python

import sys
from dae.backends.dae.loader import DaeTransmittedLoader
from dae.backends.impala.import_commons import Variants2ParquetTool


class Dae2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = DaeTransmittedLoader
    VARIANTS_TOOL = 'dae2parquet.py'


def main(argv=sys.argv[1:], gpf_instance=None, annotation_defaults={}):

    Dae2ParquetTool.main(
        argv, gpf_instance=gpf_instance,
        annotation_defaults=annotation_defaults)


if __name__ == "__main__":
    main(sys.argv[1:])
