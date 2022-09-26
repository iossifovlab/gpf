import os
import logging
from typing import Union
from dae.pedigrees.family import FamiliesData
from dae.impala_storage.parquet_io import PartitionDescriptor as Schema1PD
from dae.backends.schema2.parquet_io import PartitionDescriptor as Schema2PD


logger = logging.getLogger(__file__)


class ParquetWriter:
    """Implement writing variants and pedigrees parquet files."""

    @staticmethod
    def write_variant(variants_loader, bucket, gpf_instance, project,
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
            variants_loader,
            partition_description,
            bucket_index=bucket.index,
            rows=rows,
        )

    @staticmethod
    def write_pedigree(
        families: FamiliesData,
        out_dir: str,
        partition_description: Union[Schema1PD, Schema2PD],
        parquet_manager
    ) -> None:
        """Write FamiliesData to a pedigree parquet file."""
        if getattr(partition_description, "family_bin_size", 0) > 0:
            families = partition_description \
                .add_family_bins_to_families(families)  # type: ignore

        output_filename = os.path.join(out_dir, "pedigree.parquet")

        parquet_manager.families_to_parquet(families, output_filename)
