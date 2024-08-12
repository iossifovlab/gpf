from collections import defaultdict
from math import ceil

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.parquet.partition_descriptor import PartitionDescriptor


class MakefilePartitionHelper:
    """Helper class for organizing partition targets."""

    def __init__(
            self,
            partition_descriptor: PartitionDescriptor,
            genome: ReferenceGenome):

        self.genome = genome
        self.partition_descriptor = partition_descriptor
        self.chromosome_lengths = dict(
            self.genome.get_all_chrom_lengths(),
        )

    def region_bins_count(self, chrom: str) -> int:
        return ceil(
            self.chromosome_lengths[chrom]
            / self.partition_descriptor.region_length,
        )

    @staticmethod
    def build_target_chromosomes(target_chromosomes: list[str]) -> list[str]:
        return target_chromosomes.copy()

    def generate_chrom_targets(
            self, target_chrom: str) -> list[tuple[str, str]]:
        """Generate variant targets based on partition descriptor."""
        target = target_chrom
        if target_chrom not in self.partition_descriptor.chromosomes:
            target = "other"
        region_bins_count = self.region_bins_count(target_chrom)

        chrom = target_chrom

        if region_bins_count == 1:
            return [(f"{target}_0", chrom)]
        result = []
        for region_index in range(region_bins_count):
            start = region_index * self.partition_descriptor.region_length + 1
            end = (region_index + 1) * self.partition_descriptor.region_length
            end = min(end, self.chromosome_lengths[target_chrom])
            result.append(
                (f"{target}_{region_index}", f"{chrom}:{start}-{end}"),
            )
        return result

    def bucket_index(self, region_bin: str) -> int:
        """Return bucket index based on variants target."""
        variants_targets = self.generate_variants_targets(
            list(self.genome.get_all_chrom_lengths().keys()))
        assert region_bin in variants_targets

        targets = list(variants_targets.keys())
        return targets.index(region_bin)

    def generate_variants_targets(
            self, target_chromosomes: list[str],
            mode: str | None = None) -> dict[str, list]:
        """Produce variants targets."""
        if len(self.partition_descriptor.chromosomes) == 0:
            return {"none": [""]}

        generated_target_chromosomes = target_chromosomes.copy()
        targets: dict[str, list]
        if mode == "single_bucket":
            targets = {"all": [None]}
            return targets
        if mode == "chromosome":
            targets = {chrom: [chrom]
                       for chrom in generated_target_chromosomes}
            return targets
        if mode is not None:
            raise ValueError(f"Invalid value for mode '{mode}'")

        targets = defaultdict(list)
        for target_chrom in generated_target_chromosomes:
            assert target_chrom in self.chromosome_lengths, (
                target_chrom,
                self.chromosome_lengths,
            )
            region_targets = self.generate_chrom_targets(target_chrom)

            for target, region in region_targets:
                targets[target].append(region)
        return targets
