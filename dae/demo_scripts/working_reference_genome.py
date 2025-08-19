

def genome_from_a_file(file_name: str) -> None:
    """Example usage of reference genome from file name."""
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.reference_genome import (
        build_reference_genome_from_file,
    )
    file_genome = build_reference_genome_from_file(file_name)
    file_genome.get_sequence("chr1", 1, 10)


def genome_from_a_genomic_resource_repository(resource_id: str) -> None:
    """Example usage of reference genome from GRR."""
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources import build_genomic_resource_repository
    from dae.genomic_resources.reference_genome import (
        build_reference_genome_from_resource_id,
    )

    grr = build_genomic_resource_repository()
    ref_genome = build_reference_genome_from_resource_id(resource_id, grr)

    ref_genome.get_sequence("chr1", 1, 10)
