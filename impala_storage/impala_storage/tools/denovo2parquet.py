#!/usr/bin/env python
import sys
import logging
from typing import Optional

from dae.variants_loaders.dae.loader import DenovoLoader
from dae.gpf_instance.gpf_instance import GPFInstance

from impala_storage.schema1.import_commons import Variants2ParquetTool


logger = logging.getLogger(__name__)


class Denovo2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = DenovoLoader
    VARIANTS_TOOL = "denovo2parquet.py"

    BUCKET_INDEX_DEFAULT = 1


def main(
    argv: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None
) -> None:
    argv = argv or sys.argv[1:]
    Denovo2ParquetTool.main(
        argv,
        gpf_instance=gpf_instance
    )


if __name__ == "__main__":

    main()
