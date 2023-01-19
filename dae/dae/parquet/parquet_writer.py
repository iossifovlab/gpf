import os
import logging
from dae.pedigrees.family import FamiliesData
from dae.parquet.partition_descriptor import PartitionDescriptor


logger = logging.getLogger(__file__)


class ParquetWriter:
    """Implement writing variants and pedigrees parquet files."""

    @staticmethod
    def write_variant(
            out_dir, variants_loader, bucket, gpf_instance, project,
            partition_description, parquet_manager):
        """Write a variant to the corresponding parquet files."""
        if bucket.region_bin is not None and bucket.region_bin != "none":
            logger.info(
                "resetting regions (rb: %s): %s",
                bucket.region_bin, bucket.regions)
            variants_loader.reset_regions(bucket.regions)

        variants_loader = project.build_variants_loader_pipeline(
            variants_loader, gpf_instance
        )

        rows = project.get_row_group_size(bucket)
        logger.debug("argv.rows: %s", rows)
        parquet_manager.variants_to_parquet(
            out_dir,
            variants_loader,
            partition_description,
            bucket_index=bucket.index,
            rows=rows,
            include_reference=project.include_reference,
        )

    @staticmethod
    def write_pedigree(
        families: FamiliesData,
        out_dir: str,
        partition_descriptor: PartitionDescriptor,
        parquet_manager
    ) -> None:
        """Write FamiliesData to a pedigree parquet file."""
        output_filename = os.path.join(out_dir, "pedigree.parquet")

        parquet_manager.families_to_parquet(
            families, output_filename, partition_descriptor)
