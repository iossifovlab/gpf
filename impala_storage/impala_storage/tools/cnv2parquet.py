#!/usr/bin/env python
import sys

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants_loaders.cnv.loader import CNVLoader

from impala_storage.schema1.import_commons import Variants2ParquetTool


class Cnv2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = CNVLoader
    VARIANTS_TOOL = "cnv2parquet.py"

    BUCKET_INDEX_DEFAULT = 2


def main(
    argv: list[str] | None = None,
    gpf_instance: GPFInstance | None = None,
) -> None:
    argv = argv or sys.argv[1:]
    Cnv2ParquetTool.main(
        argv,
        gpf_instance=gpf_instance,
    )


if __name__ == "__main__":
    main()
