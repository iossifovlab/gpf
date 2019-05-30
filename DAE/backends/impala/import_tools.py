import sys
import time

from backends.impala.parquet_io import VariantsParquetWriter, \
    save_ped_df_to_parquet


def variants_iterator_to_parquet(
        fvars, impala_config, bucket_index=0,
        annotation_schema=None, filesystem=None):

    if fvars.is_empty():
        print("empty bucket {} done".format(impala_config.files.variant),
              file=sys.stderr)
        return

    save_ped_df_to_parquet(
        fvars.ped_df, impala_config.files.pedigree,
        filesystem=filesystem)

    start = time.time()
    variants_writer = VariantsParquetWriter(
        fvars.full_variants_iterator(),
        annotation_schema=annotation_schema)
    print("[DONE] going to create variants writer...")

    variants_writer.save_variants_to_parquet(
        impala_config.files.variant, filesystem=filesystem)
    end = time.time()

    print(
        "DONE: {} for {:.2f} sec".format(
            impala_config.files.variant, end-start),
        file=sys.stderr)
    return impala_config
