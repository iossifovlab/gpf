import sys
import time

from annotation.tools.file_io_parquet import ParquetSchema

from backends.configure import Configure
from backends.thrift.parquet_io import VariantsParquetWriter, \
    save_ped_df_to_parquet


def variants_iterator_to_parquet(
        fvars, parquet_prefix, bucket_index=0, annotation_pipeline=None):
    if fvars.is_empty():
        print("empty contig {} done".format(parquet_prefix), file=sys.stderr)
        return

    if annotation_pipeline is not None:
        fvars.annot_df = annotation_pipeline.annotate_df(fvars.annot_df)

    parquet_config = Configure.from_prefix_parquet(parquet_prefix).parquet
    print("converting into ", parquet_config, file=sys.stderr)

    save_ped_df_to_parquet(fvars.ped_df, parquet_config.pedigree)

    print("going to build: ", parquet_prefix, file=sys.stderr)
    start = time.time()

    annotation_schema = ParquetSchema()
    annotation_pipeline.collect_annotator_schema(annotation_schema)

    variants_writer = VariantsParquetWriter(
        fvars.full_variants_iterator(),
        annotation_schema=annotation_schema)

    variants_writer.save_variants_to_parquet(
        summary_filename=parquet_config.summary_variant,
        family_filename=parquet_config.family_variant,
        effect_gene_filename=parquet_config.effect_gene_variant,
        member_filename=parquet_config.member_variant,
        bucket_index=bucket_index)
    end = time.time()

    print("DONE: {} for {:.2f} sec".format(parquet_prefix, end-start),
          file=sys.stderr)
