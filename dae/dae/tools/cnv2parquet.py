#!/usr/bin/env python
import sys

from dae.backends.cnv.loader import CNVLoader
from dae.impala_storage.import_commons import Variants2ParquetTool


class Cnv2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = CNVLoader
    VARIANTS_TOOL = "cnv2parquet.py"

    BUCKET_INDEX_DEFAULT = 2


def main(argv=sys.argv[1:], gpf_instance=None):

    Cnv2ParquetTool.main(
        argv,
        gpf_instance=gpf_instance
    )


if __name__ == "__main__":
    main()
