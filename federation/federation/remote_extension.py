import copy
import logging
from typing import Any, cast

from dae.utils.regions import intersection
from gpf_instance.gpf_instance import WGPFInstance
from numpy import e

from dae.genomic_scores.scores import ScoreDesc
from federation.gene_sets_db import RemoteGeneSetCollection
from federation.remote_enrichment_builder import RemoteEnrichmentBuilder
from federation.remote_pheno_tool_adapter import RemotePhenoToolAdapter
from federation.remote_phenotype_data import RemotePhenotypeData
from federation.remote_study import (
    RemoteGenotypeData,
)
from federation.remote_study_wrapper import (
    RemoteWDAEStudy,
    RemoteWDAEStudyGroup,
)
from federation.rest_api_client import (
    RESTClient,
    RESTClientRequestError,
)

logger = logging.getLogger(__name__)


def load_clients(dae_config: dict[str, Any]) -> dict[str, RESTClient]:
    """Initialize REST clients for all remotes in the DAE config."""
    clients: dict[str, RESTClient] = {}

    if dae_config["remotes"] is None:
        return clients

    for remote in dae_config["remotes"]:
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
    return clients


def load_extension(instance: WGPFInstance) -> None:
    """Load remote studies and modules into a running GPF instance."""

    clients = load_clients(instance.dae_config)

    for client in clients.values():
        studies = fetch_studies_from_client(client)
        available_studies_ids = [study.study_id for study in studies]

        visible_studies = [
            client.prefix_remote_identifier(data_id)
            for data_id in client.get_visible_datasets()
        ]
        if instance.visible_datasets is None:
            instance.visible_datasets = \
                sorted(instance.get_available_data_ids())
        instance.visible_datasets.extend(visible_studies)
        for study in studies:
            logger.info("register remote study %s", study.study_id)
            instance._study_wrappers[study.study_id] = study  # noqa: SLF001
            pheno_registry = instance._pheno_registry  # noqa: SLF001

            if study.has_pheno_data:
                for candidate_study in studies:
                    if candidate_study.study_id == \
                            study.phenotype_data.pheno_id:
                        study.phenotype_data.name = candidate_study.name
                pheno_registry.register_phenotype_data(study.phenotype_data)

            if study.is_genotype:
                instance._variants_db. \
                    register_genotype_data(study.genotype_data)  # noqa: SLF001

                builder = RemoteEnrichmentBuilder(
                    instance.enrichment_helper, study.genotype_data, client,
                )
                instance.register_enrichment_builder(study.study_id, builder)

                pheno_tool_adapter = RemotePhenoToolAdapter(
                    client, study.remote_study_id,
                )
                instance.register_pheno_tool_adapter(
                    study.study_id, pheno_tool_adapter,
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
        # Important - must initialize the db first by accessing these
        # member variables, otherwise it will not load the local cache
        # since it will be non-empty because of the remote denovo gene sets
        # being loaded into the internal _collections and _configs variables
        _ = d_gs_db._denovo_gene_set_collections  # noqa: SLF001
        _ = d_gs_db._denovo_gene_set_configs  # noqa: SLF001

        remote_dgsdb_cache = {}
        for study_id, cache in client.gpf_rest_client.get_denovo_gene_sets_db().items():  # noqa: E501
            remote_id = client.prefix_remote_identifier(study_id)
            if remote_id in available_studies_ids:
                remote_dgsdb_cache[remote_id] = cache
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
) -> list[RemoteWDAEStudy]:
    """Get all remote studies from a REST client."""
    all_data = rest_client.get_datasets()
    if all_data is None:
        raise RESTClientRequestError(
            f"Failed to get studies from {rest_client.remote_id}",
        )

    genotype_data: dict[str, RemoteGenotypeData] = {}
    phenotype_data: dict[str, RemotePhenotypeData] = {}
    result: dict[str, RemoteWDAEStudy] = {}
    all_configs = {data["id"]: data for data in all_data}
    for config in all_data:
        if config["id"] in result:
            continue
        result_studies = create_remote_studies(
            rest_client,
            config,
            all_configs,
            genotype_data,
            phenotype_data,
        )
        result.update(result_studies)

    return list(result.values())

def create_remote_studies(
    rest_client: RESTClient,
    config: dict[str, Any],
    all_configs: dict[str, dict[str, Any]],
    genotype_datas: dict[str, RemoteGenotypeData],
    phenotype_datas: dict[str, RemotePhenotypeData],
) -> dict[str, RemoteWDAEStudy]:
    study_id = config["id"]
    logger.info("loading remote genotype study: %s", study_id)
    genotype_data: RemoteGenotypeData | None = None
    phenotype_data: RemotePhenotypeData | None = None
    if config.get("has_genotype"):
        if study_id not in genotype_datas:
            genotype_data = RemoteGenotypeData(
                copy.deepcopy(config), rest_client)
            genotype_datas[study_id] = genotype_data
        else:
            genotype_data = genotype_datas[study_id]

    pheno_id = cast(str | None, config.get("phenotype_data"))
    if pheno_id is not None:
        if study_id not in phenotype_datas:
            pheno_config = copy.deepcopy(config)
            pheno_config["id"] = pheno_id
            phenotype_data = RemotePhenotypeData(
                pheno_config, rest_client)
            phenotype_datas[pheno_id] = phenotype_data
        else:
            phenotype_data = phenotype_datas[pheno_id]

    if genotype_data is None and phenotype_data is not None:
        study_id = pheno_id
        if "name" in config:
            phenotype_data.name = rest_client.prefix_remote_name(config["name"])
        else:
            phenotype_data.name = None

    result: dict[str, RemoteWDAEStudy] = {}
    if config.get("studies"):
        children_ids = list(
            filter(lambda x: x != study_id, config.get("studies", [])))
        for child_id in children_ids:
            if child_id in result:
                continue
            child_studies = create_remote_studies(
                rest_client,
                all_configs[child_id],
                all_configs,
                genotype_datas,
                phenotype_datas,
            )

            if set(
                child_studies.keys()).intersection(set(result.keys()),
            ) != set():
                raise ValueError("Tried to create an already created study!")

            result.update(child_studies)
        result[study_id] = RemoteWDAEStudyGroup(
            study_id,
            rest_client,
            [result[child_id] for child_id in children_ids],
            remote_genotype_data=genotype_data,
            remote_phenotype_data=phenotype_data,
        )
    else:
        if study_id in result:
            raise ValueError("Tried to create an already created study!")

        result[study_id] = RemoteWDAEStudy(
            study_id,
            rest_client,
            remote_genotype_data=genotype_data,
            remote_phenotype_data=phenotype_data,
        )

    return result
