import itertools
import json
import logging

from abc import abstractmethod

from dae.variants.attributes import Role
from dae.studies.study import GenotypeData
from dae.configuration.gpf_config_parser import FrozenBox
from remote.remote_phenotype_data import RemotePhenotypeData
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer


logger = logging.getLogger(__name__)


class StudyWrapperBase(GenotypeData):

    def __init__(self, config):
        super(StudyWrapperBase, self).__init__(config, config.get("studies"))

    @abstractmethod
    def build_genotype_data_group_description(self, gpf_instance):
        pass

    def _build_person_set_collection(self):
        pass

    def query_variants(
        self,
        regions=None,
        genes=None,
        effect_types=None,
        family_ids=None,
        person_ids=None,
        person_set_collection=None,
        inheritance=None,
        roles=None,
        sexes=None,
        variant_type=None,
        real_attr_filter=None,
        ultra_rare=None,
        return_reference=None,
        return_unknown=None,
        limit=None,
        study_filters=None,
        affected_status=None,
        **kwargs,
    ):
        pass

    def query_summary_variants(
        self,
        regions=None,
        genes=None,
        effect_types=None,
        family_ids=None,
        person_ids=None,
        person_set_collection=None,
        inheritance=None,
        roles=None,
        sexes=None,
        variant_type=None,
        real_attr_filter=None,
        ultra_rare=None,
        return_reference=None,
        return_unknown=None,
        limit=None,
        study_filters=None,
        **kwargs,
    ):
        pass

    @abstractmethod
    def query_variants_wdae(self, kwargs, sources, max_variants_count=10000):
        pass


class StudyWrapper(StudyWrapperBase):
    def __init__(
            self, genotype_data_study, pheno_db, gene_weights_db):

        assert genotype_data_study is not None

        super(StudyWrapper, self).__init__(genotype_data_study.config)

        self.genotype_data_study = genotype_data_study

        self.is_remote = False

        self._init_wdae_config()
        self.pheno_db = pheno_db
        self._init_pheno(self.pheno_db)

        self.gene_weights_db = gene_weights_db
        self.query_transformer = QueryTransformer(self)
        self.response_transformer = ResponseTransformer(self)

    def __getattr__(self, name):
        return getattr(self.genotype_data_study, name)

    def is_group(self):
        return self.genotype_data_study.is_group()

    @property
    def families(self):
        return self.genotype_data_study.families

    @property
    def person_set_collections(self):
        return self.genotype_data_study.person_set_collections

    @property
    def person_set_collection_configs(self):
        return self.genotype_data_study._person_set_collection_configs

    def get_studies_ids(self, leafs=True):
        return self.genotype_data_study.get_studies_ids(leafs=leafs)

    def _init_wdae_config(self):
        genotype_browser_config = self.config.genotype_browser
        if not genotype_browser_config:
            return

        # PERSON AND FAMILY FILTERS
        self.person_filters = genotype_browser_config.person_filters or None
        self.family_filters = genotype_browser_config.family_filters or None

        # GENE WEIGHTS
        if genotype_browser_config.genotype:
            self.gene_weight_column_sources = [
                slot.source
                for slot in (
                    genotype_browser_config.genotype.weights.slots or []
                )
            ]
        else:
            self.gene_weight_column_sources = []

        # PRESENT IN ROLE
        self.present_in_role = genotype_browser_config.present_in_role or []

        # LEGEND
        # self.legend = {}

        # collections_conf = self.config.person_set_collections
        # if collections_conf and \
        #         collections_conf.selected_person_set_collections:
        #     for collection_id in \
        #             collections_conf.selected_person_set_collections:
        #         self.legend[collection_id] = \
        #             self.person_set_collection_configs[collection_id]["domain"]

        # PREVIEW AND DOWNLOAD COLUMNS
        self.columns = genotype_browser_config.columns
        self.column_groups = genotype_browser_config.column_groups
        self._validate_column_groups()
        self.preview_columns = genotype_browser_config.preview_columns
        self.download_columns = genotype_browser_config.download_columns
        self.summary_preview_columns = \
            genotype_browser_config.summary_preview_columns
        self.summary_download_columns = \
            genotype_browser_config.summary_download_columns

    def _init_pheno(self, pheno_db):
        self.phenotype_data = None
        if self.config.phenotype_data:
            self.phenotype_data = pheno_db.get_phenotype_data(
                self.config.phenotype_data
            )

    def _validate_column_groups(self):
        genotype_cols = self.columns.get("genotype") or list()
        phenotype_cols = self.columns.get("phenotype") or list()
        for column_group in self.column_groups.values():
            for column_id in column_group.columns:
                if column_id not in genotype_cols \
                   and column_id not in phenotype_cols:
                    logger.warn(
                        f"Column {column_id} not defined in configuration"
                    )
                    return False
        return True

    def _query_variants_rows_iterator(
            self, sources, person_set_collection, **kwargs):

        if not kwargs.get("summaryVariantIds"):
            def filter_allele(allele):
                return True
        else:
            summary_variant_ids = set(kwargs.get("summaryVariantIds"))
            # logger.debug(f"sumamry variants ids: {summary_variant_ids}")

            def filter_allele(allele):
                svid = f"{allele.cshl_location}:{allele.cshl_variant}"
                return svid in summary_variant_ids

        variants = list(self.query_variants(**kwargs))

        for v in variants:
            matched = True
            for aa in v.matched_alleles:
                assert not aa.is_reference_allele
                if not filter_allele(aa):
                    matched = False
                    break
            if not matched:
                continue

            row_variant = []

            row_variant = self.response_transformer._build_variant_row(
                v, sources, person_set_collection=person_set_collection
            )

            yield row_variant

    @property
    def config_columns(self):
        return self.config.genotype_browser.columns

    def get_columns_as_sources(self, column_ids):
        column_groups = self.config.genotype_browser.column_groups
        genotype_cols = self.config_columns.get("genotype", {})
        phenotype_cols = self.config_columns.get("phenotype", {})
        result = list()

        for column_id in column_ids:
            if column_id in column_groups:
                source_cols = column_groups[column_id].columns
            else:
                source_cols = [column_id]

            for source_col_id in source_cols:
                if source_col_id in genotype_cols:
                    result.append(genotype_cols[source_col_id])
                elif source_col_id in phenotype_cols:
                    result.append(phenotype_cols[source_col_id])

        return result

    def query_variants_wdae(self, kwargs, sources, max_variants_count=10000):
        people_group = kwargs.get("peopleGroup", {})

        person_set_collection = self.get_person_set_collection(
            people_group.get("id")  # person_set_collection_id
        )

        rows_iterator = self._query_variants_rows_iterator(
            sources, person_set_collection, **kwargs
        )

        if max_variants_count is not None:
            limited_rows = itertools.islice(rows_iterator, max_variants_count)
        else:
            limited_rows = rows_iterator

        return limited_rows

    def get_gene_view_summary_variants(self, frequency_column, **kwargs):
        kwargs = self.query_transformer.transform_kwargs(**kwargs)
        limit = None
        if "limit" in kwargs:
            limit = kwargs["limit"]

        variants_from_studies = itertools.islice(
            self.genotype_data_study.query_summary_variants(**kwargs), limit
        )
        for v in variants_from_studies:
            for a in self.response_transformer.\
               transform_gene_view_summary_variant(v, frequency_column):
                yield a

    def get_gene_view_summary_variants_download(
            self, frequency_column, **kwargs):
        kwargs = self.query_transformer.transform_kwargs(**kwargs)
        limit = None
        if "limit" in kwargs:
            limit = kwargs["limit"]

        variants_from_studies = itertools.islice(
            self.genotype_data_study.query_summary_variants(**kwargs), limit
        )
        return self.response_transformer.\
            transform_gene_view_summary_variant_download(
                variants_from_studies, frequency_column
            )

    def query_variants(self, **kwargs):
        kwargs = self.query_transformer.transform_kwargs(**kwargs)
        limit = None
        if "limit" in kwargs:
            limit = kwargs["limit"]
        logger.info(f"query filters after translation: {kwargs}")
        query_summary = kwargs.get("query_summary", False)

        if query_summary:
            variants_from_studies = itertools.islice(
                self.genotype_data_study.query_summary_variants(**kwargs),
                limit
            )
            for variant in variants_from_studies:
                yield variant
        else:
            variants_from_studies = itertools.islice(
                self.genotype_data_study.query_variants(**kwargs), limit
            )
            for variant in self.response_transformer.transform_variants(
                variants_from_studies
            ):
                yield variant

    def _get_roles_value(self, allele, roles):
        result = []
        variant_in_members = allele.variant_in_members_objects
        for role in roles:
            for member in variant_in_members:
                role = Role.from_name(role)
                if member.role == role:
                    result.append(str(role) + member.sex.short())

        return result

    # def _get_legend_default_values(self):
    #     return [
    #         {
    #             "color": "#E0E0E0",
    #             "id": "missing-person",
    #             "name": "missing-person",
    #         }
    #     ]

    # def get_legend(self, person_set_collection_id=None):
    #     if person_set_collection_id is None:
    #         legend = list(self.legend.values())[0] if self.legend else []
    #     else:
    #         legend = self.legend.get(person_set_collection_id, [])
    #     return legend + self._get_legend_default_values()

    def get_present_in_role(self, present_in_role_id):
        if not present_in_role_id:
            return {}

        return self.present_in_role.get(present_in_role_id, {})

    def build_genotype_data_group_description(self, gpf_instance):
        keys = [
            "id",
            "name",
            "phenotype_browser",
            "phenotype_tool",
            "phenotype_data",
            "common_report",
            "study_type",
            "studies",
            "has_present_in_child",
            "has_present_in_parent",
            "has_denovo",
            "genome",
            "chr_prefix",
            "gene_browser",
        ]
        result = {
            key: self.config.get(key, None) for key in keys
        }

        result["description"] = self.description

        result["genotype_browser_config"] = self.config.genotype_browser
        result["genotype_browser"] = self.config.genotype_browser.enabled

        result["study_types"] = result["study_type"]
        result["enrichment_tool"] = self.config.enrichment.enabled
        result["person_set_collections"] = \
            self.genotype_data_study.person_set_collection_configs
        result["name"] = result["name"] or result["id"]

        result["enrichment"] = self.config.enrichment.to_dict()

        result["study_names"] = None
        if result["studies"] is not None:
            logger.debug(f"found studies in {self.config.id}")
            study_names = []
            for studyId in result["studies"]:
                wrapper = gpf_instance.get_wdae_wrapper(studyId)
                name = (
                    wrapper.config.name
                    if wrapper.config.name is not None
                    else wrapper.config.id
                )
                study_names.append(name)
                result["study_names"] = study_names

        return result


class RemoteStudyWrapper(StudyWrapperBase):

    def __init__(self, study_id, rest_client):
        self._remote_study_id = study_id
        self.rest_client = rest_client

        config = self.rest_client.get_dataset_config(self._remote_study_id)
        config["id"] = self.rest_client.prefix_remote_identifier(study_id)
        config["name"] = self.rest_client.prefix_remote_name(config["name"])
        del config["access_rights"]
        del config["groups"]
        if config["parents"]:
            config["parents"] = list(
                map(
                    self.rest_client.prefix_remote_identifier,
                    config["parents"]
                )
            )

        if config.get("studies"):
            config["studies"] = list(
                map(
                    self.rest_client.prefix_remote_identifier,
                    config["studies"]
                )
            )

        super(RemoteStudyWrapper, self).__init__(FrozenBox(config))

        self.phenotype_data = RemotePhenotypeData(
            self._remote_study_id,
            self.rest_client
        )

        self.is_remote = True

    def is_group(self):
        pass

    def families(self):
        pass

    def get_studies_ids(self, leafs=True):
        studies = self.config["studies"]
        if not studies:
            return []
        return studies

    def query_variants_wdae(self, kwargs, sources, max_variants_count=10000):
        study_filters = kwargs.get("study_filters")
        logger.debug(
            f"study_id: {self.study_id}; study_filters: {study_filters}")
        if study_filters is not None:
            del kwargs["study_filters"]
        if kwargs.get("allowed_studies"):
            del kwargs["allowed_studies"]

        kwargs["datasetId"] = self._remote_study_id
        kwargs["maxVariantsCount"] = max_variants_count
        kwargs["sources"] = sources

        response = self.rest_client.post_query_variants(kwargs)
        for line in response.iter_lines():
            if line:
                variants = json.loads(line)
                for variant in variants:
                    yield variant

    def build_genotype_data_group_description(self, gpf_instance):
        return self.config.to_dict()
