import logging

from gpf_instance.gpf_instance import WGPFInstance

from dae.genomic_scores.scores import ScoreDesc
from federation.remote.gene_sets_db import RemoteGeneSetCollection
from federation.remote.remote_enrichment_builder import RemoteEnrichmentBuilder
from federation.remote.remote_pheno_tool_adapter import RemotePhenoToolAdapter
from federation.remote.remote_study import RemoteGenotypeData
from federation.remote.remote_study_wrapper import RemoteStudyWrapper
from federation.remote.rest_api_client import (
    RESTClient,
    RESTClientRequestError,
)

logger = logging.getLogger(__name__)


def load_extension(instance: WGPFInstance) -> None:
    """Load remote studies and modules into a running GPF instance."""
    clients: dict[str, RESTClient] = {}
    remotes = instance.dae_config.remotes
    if remotes is not None:
        for remote in remotes:
            logger.info("Creating remote %s", remote)
            try:
                client = RESTClient(
                    remote["id"],
                    remote["host"],
                    remote["credentials"],
                    base_url=remote["base_url"],
                    port=remote.get("port", None),
                    protocol=remote.get("protocol", None),
                    gpf_prefix=remote.get("gpf_prefix", None),
                )
                clients[client.remote_id] = client

            except ConnectionError:
                logger.exception("Failed to create remote %s", remote["id"])

    for client in clients.values():
        studies = fetch_studies_from_client(client)
        for study in studies:
            wrapper = RemoteStudyWrapper(study)

            instance.register_genotype_data(study, study_wrapper=wrapper)
            pheno_registry = instance._pheno_registry  # noqa: SLF001

            if wrapper.phenotype_data is not None:
                pheno_registry.register_phenotype_data(
                    wrapper.phenotype_data,
                )
            if instance.visible_datasets is not None:
                instance.visible_datasets.append(wrapper.study_id)

            builder = RemoteEnrichmentBuilder(
                instance.enrichment_helper, wrapper, client,
            )

            instance.register_enrichment_builder(wrapper.study_id, builder)

            pheno_tool_adapter = RemotePhenoToolAdapter(
                client, wrapper.remote_study_id,
            )

            instance.register_pheno_tool_adapter(
                wrapper.study_id, pheno_tool_adapter,
            )

        gs_db = instance.gene_sets_db
        for collection in client.get_gene_set_collections():
            gsc_id = collection["name"]
            if gsc_id == "denovo":
                continue
            gsc_desc = collection["desc"]
            gsc_fmt = collection["format"]
            gsc = RemoteGeneSetCollection(
                gsc_id, client, gsc_desc, gsc_fmt,
            )
            gsc_id = gsc.collection_id
            gs_db.gene_set_collections[gsc_id] = gsc

        scores = client.get_genomic_scores()
        if scores is not None:
            for score in scores:
                desc = score.get("description")
                score["name"] = client.prefix_remote_identifier(score["name"])
                if desc is None:
                    desc = score["name"]
                else:
                    score["description"] = client.prefix_remote_name(
                        desc,
                    )

                instance.genomic_scores.scores[score["name"]] = \
                    ScoreDesc.from_json(score)


def fetch_studies_from_client(
    rest_client: RESTClient,
) -> list[RemoteGenotypeData]:
    """Get all remote studies from a REST client."""
    studies = []
    fetched_studies = rest_client.get_studies()
    if fetched_studies is None:
        raise RESTClientRequestError(
            f"Failed to get studies from {rest_client.remote_id}",
        )
    for study in fetched_studies["data"]:
        logger.info("creating remote genotype data: %s", study["id"])
        studies.append(RemoteGenotypeData(study["id"], rest_client))

    return studies
