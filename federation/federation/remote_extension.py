import logging

from gpf_instance.gpf_instance import WGPFInstance

from dae.genomic_scores.scores import ScoreDesc
from federation.gene_sets_db import RemoteGeneSetCollection
from federation.remote_enrichment_builder import RemoteEnrichmentBuilder
from federation.remote_pheno_tool_adapter import RemotePhenoToolAdapter
from federation.remote_study import (
    RemoteGenotypeData,
    RemoteGenotypeDataGroup,
)
from federation.remote_study_wrapper import RemoteStudyWrapper
from federation.rest_api_client import (
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
                    remote["client_id"],
                    remote["client_secret"],
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
        visible_studies = [
            client.prefix_remote_identifier(data_id)
            for data_id in client.get_visible_datasets()
        ]
        if instance.visible_datasets is None:
            instance.visible_datasets = \
                sorted(instance.get_available_data_ids())
        instance.visible_datasets.extend(visible_studies)
        for study in studies:
            wrapper = RemoteStudyWrapper(study)

            instance._variants_db.register_genotype_data(study)  # noqa: SLF001
            instance._study_wrappers[wrapper.study_id] = wrapper  # noqa: SLF001
            pheno_registry = instance._pheno_registry  # noqa: SLF001

            if wrapper.has_pheno_data:
                pheno_registry._cache[wrapper.phenotype_data.pheno_id] = \
                    wrapper.phenotype_data  # noqa: SLF001

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
            gsc_fmt = "|".join(collection["format"])
            gsc = RemoteGeneSetCollection(
                gsc_id, client, gsc_desc, gsc_fmt,
            )
            gsc_id = gsc.collection_id
            gs_db.gene_set_collections[gsc_id] = gsc

        d_gs_db = instance.denovo_gene_sets_db
        remote_dgsdb_cache = {
            client.prefix_remote_identifier(study_id): cache
            for study_id, cache in client.gpf_rest_client.get_denovo_gene_sets_db().items()  # noqa: E501
        }
        d_gs_db.update_cache(remote_dgsdb_cache)

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
    result = {}

    all_data = rest_client.get_datasets()
    if all_data is None:
        raise RESTClientRequestError(
            f"Failed to get studies from {rest_client.remote_id}",
        )

    for config in all_data:
        study_id = config["id"]
        if config is None:
            raise ValueError(f"unable to find remote study {study_id}")
        logger.info("creating remote genotype study: %s", study_id)
        if "studies" in config:
            data = RemoteGenotypeDataGroup(study_id, config, rest_client)
        else:
            data = RemoteGenotypeData(study_id, config, rest_client)
        result[study_id] = data

    for data in result.values():
        if not isinstance(data, RemoteGenotypeDataGroup):
            continue
        data.studies = [
            result[child_id]
            for child_id in data.config["studies"]
        ]

    return list(result.values())
