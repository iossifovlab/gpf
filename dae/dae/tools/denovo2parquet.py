#!/usr/bin/env python
import sys

from dae.backends.dae.loader import DenovoLoader
from dae.backends.impala.import_commons import Variants2ParquetTool


class Denovo2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = DenovoLoader
    VARIANTS_TOOL = 'denovo2parquet.py'

    BUCKET_INDEX_DEFAULT = 1


def main(argv=sys.argv[1:], gpf_instance=None, annotation_defaults={}):

    Denovo2ParquetTool.main(
        argv, gpf_instance=gpf_instance,
        annotation_defaults=annotation_defaults)


if __name__ == "__main__":
    main()
