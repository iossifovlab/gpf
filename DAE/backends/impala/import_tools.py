import sys
import time

from backends.configure import Configure
from backends.impala.parquet_io import VariantsParquetWriter, \
    save_ped_df_to_parquet


def variants_iterator_to_parquet(
        fvars, parquet_prefix, bucket_index=0,
        annotation_schema=None, filesystem=None):

    if fvars.is_empty():
        print("empty bucket {} done".format(parquet_prefix), file=sys.stderr)
        return

    impala_config = Configure.from_prefix_impala(
        parquet_prefix, bucket_index=bucket_index, db=None).impala

    print("converting into ", impala_config, file=sys.stderr)

    save_ped_df_to_parquet(
        fvars.ped_df, impala_config.files.pedigree,
        filesystem=filesystem)

    start = time.time()
    print("going to create variants writer...")
    variants_writer = VariantsParquetWriter(
        fvars.full_variants_iterator(),
        annotation_schema=annotation_schema)
    print("[DONE] going to create variants writer...")

    variants_writer.save_variants_to_parquet(
        impala_config.files.variants, filesystem=filesystem)
    end = time.time()

    print("DONE: {} for {:.2f} sec".format(parquet_prefix, end-start),
          file=sys.stderr)
    return impala_config
