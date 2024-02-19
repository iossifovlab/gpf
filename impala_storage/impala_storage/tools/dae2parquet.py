#!/usr/bin/env python
import logging
import sys
from typing import Optional

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants_loaders.dae.loader import DaeTransmittedLoader
from impala_storage.schema1.import_commons import Variants2ParquetTool


logger = logging.getLogger(__name__)


class Dae2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = DaeTransmittedLoader
    VARIANTS_TOOL = "dae2parquet.py"
    VARIANTS_FREQUENCIES = False


def main(
    argv: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None
) -> None:
    argv = argv or sys.argv[1:]
    Dae2ParquetTool.main(
        argv,
        gpf_instance=gpf_instance
    )


if __name__ == "__main__":
    main(sys.argv[1:])
