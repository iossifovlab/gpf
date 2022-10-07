#!/usr/bin/env python
import sys
import logging

from dae.variants_loaders.vcf.loader import VcfLoader
from dae.impala_storage.schema1.import_commons import Variants2ParquetTool


logger = logging.getLogger("vcf2parquet")


class Vcf2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = VcfLoader
    VARIANTS_TOOL = "vcf2parquet.py"
    VARIANTS_FREQUENCIES = True


def main(argv=None, gpf_instance=None):

    Vcf2ParquetTool.main(
        argv or sys.argv[1:],
        gpf_instance=gpf_instance
    )


if __name__ == "__main__":
    main()
