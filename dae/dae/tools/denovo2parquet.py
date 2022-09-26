#!/usr/bin/env python
import sys
import logging

from dae.backends.dae.loader import DenovoLoader
from dae.impala_storage.import_commons import Variants2ParquetTool


logger = logging.getLogger(__name__)


class Denovo2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = DenovoLoader
    VARIANTS_TOOL = "denovo2parquet.py"

    BUCKET_INDEX_DEFAULT = 1


def main(argv=sys.argv[1:], gpf_instance=None):

    Denovo2ParquetTool.main(
        argv,
        gpf_instance=gpf_instance
    )


if __name__ == "__main__":

    main()
