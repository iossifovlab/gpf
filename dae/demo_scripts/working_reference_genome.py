from typing import cast


def genome_from_a_file(file_name: str) -> None:
    from dae.genomic_resources.reference_genome import open_ref
    file_genome = open_ref(file_name)
    file_genome.get_sequence("chr1", 1, 10)


def genome_from_a_genomic_resource_repository(resource_id) -> None:
    from dae.genomic_resources import build_genomic_resource_repository
    from dae.genomic_resources.reference_genome_resource import \
        ReferenceGenomeResource

    grr = build_genomic_resource_repository()
    resource = grr.get_resource(resource_id)

    if resource is None or not isinstance(resource, ReferenceGenomeResource):
        raise Exception('failed')
    ref_genome_resource = cast(ReferenceGenomeResource, resource)
    ref_genome = ref_genome_resource.open()

    ref_genome.get_sequence
