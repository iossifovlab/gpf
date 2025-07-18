#!/usr/bin/env python
import logging
import sys

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants_loaders.vcf.loader import VcfLoader

from impala_storage.schema1.import_commons import Variants2ParquetTool

logger = logging.getLogger("vcf2parquet")


class Vcf2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = VcfLoader
    VARIANTS_TOOL = "vcf2parquet.py"
    VARIANTS_FREQUENCIES = True


def main(
    argv: list[str] | None = None,
    gpf_instance: GPFInstance | None = None,
) -> None:

    Vcf2ParquetTool.main(
        argv or sys.argv[1:],
        gpf_instance=gpf_instance,
    )


if __name__ == "__main__":
    main()
