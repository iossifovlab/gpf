#!/usr/bin/env python
import logging

import sys
from dae.backends.dae.loader import DaeTransmittedLoader
from dae.impala_storage.import_commons import Variants2ParquetTool


logger = logging.getLogger(__name__)


class Dae2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = DaeTransmittedLoader
    VARIANTS_TOOL = "dae2parquet.py"
    VARIANTS_FREQUENCIES = False


def main(argv=sys.argv[1:], gpf_instance=None):

    Dae2ParquetTool.main(
        argv,
        gpf_instance=gpf_instance
    )


if __name__ == "__main__":
    main(sys.argv[1:])
