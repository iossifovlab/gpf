

def genome_from_a_file(file_name: str) -> None:
    from dae.genomic_resources.reference_genome import (
        open_reference_genome_from_file,
    )
    file_genome = open_reference_genome_from_file(file_name)
    file_genome.get_sequence("chr1", 1, 10)


def genome_from_a_genomic_resource_repository(resource_id) -> None:
    from dae.genomic_resources import build_genomic_resource_repository
    from dae.genomic_resources.reference_genome import (
        open_reference_genome_from_resource,
    )

    grr = build_genomic_resource_repository()
    resource = grr.get_resource(resource_id)
    ref_genome = open_reference_genome_from_resource(resource)

    ref_genome.get_sequence("chr1", 1, 10)
