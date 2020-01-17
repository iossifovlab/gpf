#!/usr/bin/env python
import sys

from dae.backends.vcf.loader import VcfLoader
from dae.backends.impala.import_commons import Variants2ParquetTool


class Vcf2ParquetTool(Variants2ParquetTool):

    VARIANTS_LOADER_CLASS = VcfLoader
    VARIANTS_TOOL = 'vcf2parquet.py'
    VARIANTS_FREQUENCIES = True


def main(argv=sys.argv[1:], gpf_instance=None, annotation_defaults={}):

    Vcf2ParquetTool.main(
        argv, gpf_instance=gpf_instance,
        annotation_defaults=annotation_defaults)


if __name__ == "__main__":
    main()
