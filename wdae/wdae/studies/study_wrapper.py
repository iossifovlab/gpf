import time
import itertools
import logging
from contextlib import closing
from abc import abstractmethod
from typing import Optional, Any, Iterable, Generator, cast

from box import Box

from remote.remote_phenotype_data import RemotePhenotypeData
from remote.remote_variant import RemoteFamilyVariant, QUERY_SOURCES
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer
from studies.remote_study import RemoteGenotypeData

from dae.pedigrees.families_data import FamiliesData
from dae.person_sets import PersonSetCollection
from dae.variants.attributes import Role
from dae.variants.family_variant import FamilyAllele
from dae.studies.study import GenotypeData
from dae.pheno.registry import PhenoRegistry
from dae.pheno.pheno_data import PhenotypeData
from dae.gene_scores.gene_scores import GeneScoresDb


logger = logging.getLogger(__name__)


class StudyWrapperBase:
    """Defines WDAE wrapper class to DAE genotype data object."""

    def __init__(self, genotype_data: GenotypeData):
        self.genotype_data = genotype_data
        self.config = self.genotype_data.config
        assert self.config is not None, self.genotype_data.study_id

    @property
    def study_id(self) -> str:
        return self.genotype_data.study_id

    @property
    def description(self) -> Optional[str]:
        return self.genotype_data.description

    @staticmethod
    def get_columns_as_sources(
        config: Box, column_ids: list[str]
    ) -> list[dict[str, Any]]:
        """Return the list of column sources."""
        column_groups = config.genotype_browser.column_groups
        genotype_cols = config.genotype_browser.columns.get("genotype", {})
        if genotype_cols is None:
            genotype_cols = {}
        phenotype_cols = config.genotype_browser.columns.get("phenotype", {})
        if phenotype_cols is None:
            phenotype_cols = {}
        result = []

        for column_id in column_ids:
            if column_id in column_groups:
                source_cols = column_groups[column_id].columns
            else:
                source_cols = [column_id]

            for source_col_id in source_cols:
                if source_col_id in genotype_cols:
                    result.append(dict(genotype_cols[source_col_id]))
                elif source_col_id in phenotype_cols:
                    result.append(dict(phenotype_cols[source_col_id]))

        return result

    @staticmethod
    def build_genotype_data_all_datasets(config: Box) -> dict[str, Any]:
        """Prepare response for all genotype datasets."""
        keys = [
            "id",
            "name",
            "phenotype_browser",
            "phenotype_tool"
        ]
        result = {
            key: config.get(key, None) for key in keys
        }
        result["name"] = result["name"] or result["id"]
        result["genotype_browser"] = config.genotype_browser.enabled
        result["common_report"] = {"enabled": config.common_report.enabled}
        result["enrichment_tool"] = config.enrichment.enabled
        result["gene_browser"] = {"enabled": config.gene_browser.enabled}

        return result

    @staticmethod
    def build_genotype_data_description(
        gpf_instance: Any,
        config: Box,
        description: Optional[str],
        person_set_collection_configs: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build and return genotype data group description."""
        keys = [
            "id",
            "name",
            "phenotype_browser",
            "phenotype_tool",
            "phenotype_data",
            "study_type",
            "studies",
            "has_present_in_child",
            "has_present_in_parent",
            "has_denovo",
            "genome",
            "chr_prefix",
            "gene_browser",
            "description_editable"
        ]
        result = {
            key: config.get(key, None) for key in keys
        }

        result["description"] = description

        result["genotype_browser"] = config.genotype_browser.enabled
        result["genotype_browser_config"] = {
            key: config.genotype_browser.get(key, None) for key in [
                "has_family_filters",
                "has_person_filters",
                "has_study_filters",
                "has_present_in_child",
                "has_present_in_parent",
                "has_pedigree_selector",
                "variant_types",
                "selected_variant_types",
                "max_variants_count",
                "person_filters",
                "family_filters",
                "genotype",
                "inheritance_type_filter",
                "selected_inheritance_type_filter_values",
            ]
        }

        # TODO Code below could be made a bit leaner and separated
        table_columns = []
        for column in config.genotype_browser.preview_columns:
            logger.info(
                "processing preview column %s for study %s", column, config.id)

            if column in config.genotype_browser.column_groups:
                new_col = dict(config.genotype_browser.column_groups[column])
                new_col["columns"] = StudyWrapperBase.get_columns_as_sources(
                    config, [column]  # FIXME Hacky way of using that method
                )
                table_columns.append(new_col)
            else:
                if config.genotype_browser.columns.genotype and \
                        column in config.genotype_browser.columns.genotype:
                    table_columns.append(
                        dict(config.genotype_browser.columns.genotype[column])
                    )
                elif config.genotype_browser.columns.phenotype and \
                        column in config.genotype_browser.columns.phenotype:
                    table_columns.append(
                        dict(config.genotype_browser.columns.phenotype[column])
                    )
                else:
                    raise KeyError(f"No such column {column} configured!")
        result["genotype_browser_config"]["table_columns"] = table_columns

        result["study_types"] = result["study_type"]
        result["enrichment_tool"] = config.enrichment.enabled
        result["common_report"] = config.common_report.to_dict()
        del result["common_report"]["file_path"]
        result["person_set_collections"] = person_set_collection_configs
        result["name"] = result["name"] or result["id"]

        result["enrichment"] = config.enrichment.to_dict()
        if "background" in result["enrichment"]:
            if "coding_len_background_model" in \
                    result["enrichment"]["background"].keys():
                del result["enrichment"]["background"][
                    "coding_len_background_model"]["file"]
            if "samocha_background_model" in \
                    result["enrichment"]["background"].keys():
                del result["enrichment"]["background"][
                    "samocha_background_model"]["file"]

        result["study_names"] = None
        if result["studies"] is not None:
            logger.debug("found studies in %s", config.id)
            study_names = []
            for study_id in result["studies"]:
                wrapper = gpf_instance.get_wdae_wrapper(study_id)
                if wrapper is None:
                    logger.warning(
                        "no wrapper found for study %s", study_id)
                    continue
                name = (
                    wrapper.config.name
                    if wrapper.config.name is not None
                    else wrapper.config.id
                )
                study_names.append(name)
                result["study_names"] = study_names

        return result

    def query_variants_wdae(
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        max_variants_count: int = 10000,
        max_variants_message: bool = False
    ) -> Iterable[list]:
        """Wrap query variants method for WDAE streaming."""
        variants_result = self.query_variants_wdae_streaming(
            kwargs, sources, max_variants_count,
            max_variants_message)
        return filter(None, variants_result)

    @abstractmethod
    def query_variants_wdae_streaming(
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        max_variants_count: int = 10000,
        max_variants_message: bool = False
    ) -> Generator[Optional[list], None, None]:
        """Wrap query variants method for WDAE streaming."""

    @abstractmethod
    def has_pheno_data(self) -> bool:
        raise NotImplementedError()


class StudyWrapper(StudyWrapperBase):
    """Genotype data study wrapper class for WDAE."""

    # pylint: disable=too-many-instance-attributes
    def __init__(  # type: ignore
        self, genotype_data_study: GenotypeData,
        pheno_db: PhenoRegistry,
        gene_scores_db: GeneScoresDb,
        gpf_instance
    ) -> None:

        assert genotype_data_study is not None

        super().__init__(genotype_data_study)

        self.genotype_data_study = genotype_data_study

        self.is_remote = False

        self._init_wdae_config()
        self.pheno_db = pheno_db
        self._init_pheno(self.pheno_db)

        self.gene_scores_db = gene_scores_db
        self.gpf_instance = gpf_instance
        self.query_transformer = QueryTransformer(self)
        self.response_transformer = ResponseTransformer(self)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.genotype_data_study, name)

    @property
    def is_group(self) -> bool:
        return self.genotype_data_study.is_group

    @property
    def families(self) -> FamiliesData:
        return self.genotype_data_study.families

    @property
    def person_set_collections(self) -> dict[str, PersonSetCollection]:
        return self.genotype_data_study.person_set_collections

    def get_studies_ids(self, leaves: bool = True) -> list[str]:
        return self.genotype_data_study.get_studies_ids(leaves=leaves)

    def _init_wdae_config(self) -> None:
        genotype_browser_config = self.config.genotype_browser
        if not genotype_browser_config:
            return

        # PERSON AND FAMILY FILTERS
        self.person_filters = genotype_browser_config.person_filters or None
        self.family_filters = genotype_browser_config.family_filters or None

        # GENE SCORES
        if genotype_browser_config.column_groups and \
                genotype_browser_config.column_groups.gene_scores:
            self.gene_score_column_sources = [
                genotype_browser_config.columns.genotype[slot].source
                for slot in (
                    genotype_browser_config.column_groups.gene_scores.columns
                    or []
                )
            ]
        else:
            self.gene_score_column_sources = []

        # PREVIEW AND DOWNLOAD COLUMNS
        self.columns = genotype_browser_config.columns
        self.column_groups = genotype_browser_config.column_groups
        self._validate_column_groups()
        self.preview_columns = genotype_browser_config.preview_columns
        if genotype_browser_config.preview_columns_ext:
            self.preview_columns.extend(
                genotype_browser_config.preview_columns_ext)
        self.download_columns = genotype_browser_config.download_columns
        if genotype_browser_config.download_columns_ext:
            self.download_columns.extend(
                genotype_browser_config.download_columns_ext)

        self.summary_preview_columns = \
            genotype_browser_config.summary_preview_columns
        self.summary_download_columns = \
            genotype_browser_config.summary_download_columns

    def _init_pheno(self, pheno_db: Optional[PhenoRegistry]) -> None:
        self.phenotype_data: Optional[PhenotypeData] = None
        if pheno_db is None:
            return
        if self.config.phenotype_data:
            self.phenotype_data = pheno_db.get_phenotype_data(
                self.config.phenotype_data
            )

    def _validate_column_groups(self) -> bool:
        genotype_cols = self.columns.get("genotype") or []
        phenotype_cols = self.columns.get("phenotype") or []
        for column_group_name, column_group in self.column_groups.items():
            if column_group is None:
                logger.warning(
                    "bad configuration for column group %s",
                    column_group_name)
                continue
            for column_id in column_group.columns:
                if column_id not in genotype_cols \
                   and column_id not in phenotype_cols:
                    logger.warning(
                        "column %s not defined in configuration", column_id)
                    return False
        return True

    def has_pheno_data(self) -> bool:
        return self.phenotype_data is not None

    @property
    def config_columns(self) -> Box:
        return cast(Box, self.config.genotype_browser.columns)

    def transform_request(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        return self.query_transformer.transform_kwargs(**kwargs)

    def query_variants_wdae_streaming(  # noqa
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        max_variants_count: int = 10000,
        max_variants_message: bool = False
    ) -> Generator[Optional[list], None, None]:
        """Wrap query variants method for WDAE streaming of variants."""
        # pylint: disable=too-many-locals,too-many-branches
        max_variants_count = kwargs.pop("maxVariantsCount", max_variants_count)
        summary_variant_ids = kwargs.pop("summaryVariantIds", None)
        kwargs = self.query_transformer.transform_kwargs(**kwargs)

        if summary_variant_ids is None:
            def filter_allele(
                allele: FamilyAllele  # pylint: disable=unused-argument
            ) -> bool:
                return True

        elif len(summary_variant_ids) > 0:
            summary_variant_ids = set(summary_variant_ids)

            def filter_allele(allele: FamilyAllele) -> bool:
                svid = f"{allele.cshl_location}:{allele.cshl_variant}"
                return svid in summary_variant_ids

        else:
            # passed empty list of summary variants; empty result
            return

        start = time.time()
        logger.debug(
            "study wrapper (%s) creating variant transformer...",
            self.name)
        transform = self.response_transformer.variant_transformer()
        logger.debug(
            "study wrapper (%s) variant transformer created in %.2f sec",
            self.name, time.time() - start)

        index = 0
        seen = set()
        unique_family_variants = kwargs.get("unique_family_variants", False)

        try:
            started = time.time()
            logger.debug(
                "study wrapper (%s) creating query_result_variants...",
                self.name)
            variants_result = \
                self.genotype_data_study.query_result_variants(
                    limit=max_variants_count, **kwargs)
            if variants_result is None:
                return

            logger.debug(
                "study wrapper (%s) starting query_result_variants...",
                self.name)
            variants_result.start()
            elapsed = time.time() - started
            logger.info(
                "study wrapper (%s) variant result started in %0.3fsec",
                self.name, elapsed)

            with closing(variants_result) as variants:
                for variant in variants:
                    if variant is None:
                        yield None
                        continue
                    v = transform(variant)

                    matched = True
                    for aa in v.matched_alleles:
                        assert not aa.is_reference_allele
                        if not filter_allele(cast(FamilyAllele, aa)):
                            matched = False
                            break
                    if not matched:
                        yield None
                        continue

                    fvuid = variant.fvuid
                    if unique_family_variants and fvuid in seen:
                        continue
                    seen.add(fvuid)

                    index += 1
                    if max_variants_count and index > max_variants_count:
                        if max_variants_message:
                            yield [
                                f"# limit of {max_variants_count} variants "
                                f"reached"
                            ]
                        break
                    row_variant = self.response_transformer.build_variant_row(
                        v, sources,
                        person_set_collection=kwargs.get(
                            "person_set_collection", (None, None))[0]
                    )

                    yield row_variant
        except GeneratorExit:
            pass
        finally:
            elapsed = time.time() - started
            logger.info(
                "study wrapper (%s)  query returned %s variants; "
                "closed in %0.3fsec", self.study_id, index, elapsed)

    def get_gene_view_summary_variants(
        self, frequency_column: str, **kwargs: Any
    ) -> Generator[dict[str, Any], None, None]:
        """Return gene browser summary variants."""
        kwargs = self.query_transformer.transform_kwargs(**kwargs)
        limit = kwargs.pop("maxVariantsCount", None)
        variants_from_studies = itertools.islice(
            self.genotype_data_study.query_summary_variants(
                **kwargs),
            cast(Optional[int], limit)
        )
        for v in variants_from_studies:
            for aa in self.response_transformer.\
                    transform_gene_view_summary_variant(v, frequency_column):
                yield aa

    def get_gene_view_summary_variants_download(
        self, frequency_column: str,
        **kwargs: Any
    ) -> Iterable:
        """Return gene browser summary variants for downloading."""
        kwargs = self.query_transformer.transform_kwargs(**kwargs)
        limit = kwargs.get("limit", None)

        summary_variant_ids = set(kwargs["summaryVariantIds"])
        variants_from_studies = itertools.islice(
            self.genotype_data_study.query_summary_variants(**kwargs), limit
        )
        return self.response_transformer.\
            transform_gene_view_summary_variant_download(
                variants_from_studies, frequency_column, summary_variant_ids
            )

    @staticmethod
    def _get_roles_value(allele: FamilyAllele, roles: list[str]) -> list[str]:
        result = []
        variant_in_members = allele.variant_in_members_objects
        for role_name in roles:
            for member in variant_in_members:
                role = Role.from_name(role_name)
                assert role is not None
                if member.role == role:
                    result.append(str(role) + member.sex.short())

        return result


class RemoteStudyWrapper(StudyWrapperBase):
    """Wrapper class for remote (federation) studies."""

    def __init__(self, remote_genotype_data: RemoteGenotypeData):
        self.remote_genotype_data = remote_genotype_data
        self._remote_study_id = remote_genotype_data._remote_study_id
        self.rest_client = remote_genotype_data.rest_client

        super().__init__(remote_genotype_data)

        self.phenotype_data = None
        pheno_id = self.config.get("phenotype_data")
        if pheno_id:
            self.phenotype_data = RemotePhenotypeData(
                pheno_id,
                self._remote_study_id,
                self.rest_client
            )

        self.is_remote = True

        self._person_set_collections = None
        self._person_set_collection_configs = None

        self.response_transformer = ResponseTransformer(self)

    @property
    def is_group(self) -> bool:
        return self.remote_genotype_data.is_group

    @property
    def person_set_collections(self) -> dict[str, PersonSetCollection]:
        return self.remote_genotype_data.person_set_collections

    @property
    def config_columns(self) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            self.config.genotype_browser.columns)

    @property
    def families(self) -> FamiliesData:
        # pylint: disable=protected-access
        return self.remote_genotype_data._families

    @property
    def parents(self) -> set[str]:
        return self.remote_genotype_data.parents

    @property
    def name(self) -> str:
        return self.remote_genotype_data.name

    def has_pheno_data(self) -> bool:
        return self.phenotype_data is not None

    def get_studies_ids(self, leaves: bool = True) -> list[str]:
        return self.remote_genotype_data.get_studies_ids(leaves=leaves)

    def query_variants_wdae_streaming(
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        max_variants_count: int = 10000,
        max_variants_message: bool = False
    ) -> Generator[list, None, None]:
        study_filters = kwargs.get("study_filters")
        person_set_collection_id = \
            kwargs.get("personSetCollection", {}).get("id")

        if study_filters is not None:
            del kwargs["study_filters"]
        if kwargs.get("allowed_studies"):
            del kwargs["allowed_studies"]

        kwargs["datasetId"] = self._remote_study_id
        kwargs["maxVariantsCount"] = max_variants_count
        new_sources = []
        for query_s in QUERY_SOURCES:
            if not any(query_s["source"] == s["source"] for s in sources):
                new_sources.append(query_s)
        sources.extend(new_sources)
        kwargs["sources"] = sources

        fam_id_idx = -1
        for idx, source in enumerate(sources):
            if source["source"] == "family":
                fam_id_idx = idx
                break

        assert fam_id_idx >= 0, fam_id_idx

        response = self.rest_client.post_query_variants(
            kwargs, reduce_alleles=False
        )

        for source in sources:
            if "format" in source:
                del source["format"]

        def get_source(col: dict[str, Any]) -> Any:
            res = col["source"]
            if "role" in col:
                res = f"{res}.{col['role']}"
            return res

        for variant in response:
            fam_id = variant[fam_id_idx][0]
            family = self.families[fam_id]
            fv = RemoteFamilyVariant(
                variant, family, list(map(get_source, sources)))
            # pylint: disable=protected-access
            row_variant = self.response_transformer.build_variant_row(
                fv, sources, person_set_collection=person_set_collection_id)

            yield row_variant

    def get_person_set_collection(
        self, person_set_collection_id: str
    ) -> Optional[PersonSetCollection]:
        return self.remote_genotype_data.get_person_set_collection(
            person_set_collection_id
        )
