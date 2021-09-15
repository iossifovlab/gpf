import itertools
import logging

from abc import abstractmethod

from dae.variants.attributes import Role
from remote.remote_phenotype_data import RemotePhenotypeData
from remote.remote_variant import RemoteFamilyVariant, QUERY_SOURCES
from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer


logger = logging.getLogger(__name__)


class StudyWrapperBase:

    def __init__(self, genotype_data):
        self.genotype_data = genotype_data
        self.config = self.genotype_data.config

    @property
    def study_id(self):
        return self.genotype_data.study_id

    @property
    def description(self):
        return self.genotype_data.description

    @property
    def person_set_collection_configs(self):
        return self.genotype_data.person_set_collection_configs

    @staticmethod
    def get_columns_as_sources(config, column_ids):
        column_groups = config.genotype_browser.column_groups
        genotype_cols = config.genotype_browser.columns.get("genotype", {})
        if genotype_cols is None:
            genotype_cols = {}
        phenotype_cols = config.genotype_browser.columns.get("phenotype", {})
        if phenotype_cols is None:
            phenotype_cols = {}
        result = list()

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
    def build_genotype_data_group_description(
        gpf_instance, config, description, person_set_collection_configs
    ):
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
        table_columns = list()
        for column in config.genotype_browser.preview_columns:
            logger.info(
                f"processing preview column {column} "
                f"for study {config.id}")

            if column in config.genotype_browser.column_groups:
                new_col = dict(config.genotype_browser.column_groups[column])
                new_col['columns'] = StudyWrapperBase.get_columns_as_sources(
                    config, [column]  # FIXME Hacky way of using that method
                )
                table_columns.append(new_col)
            else:
                if column in config.genotype_browser.columns.genotype:
                    table_columns.append(
                        dict(config.genotype_browser.columns.genotype[column])
                    )
                elif column in config.genotype_browser.columns.phenotype:
                    table_columns.append(
                        dict(config.genotype_browser.columns.phenotype[column])
                    )
                else:
                    raise KeyError(f"No such column {column} configured!")
        result["genotype_browser_config"]["table_columns"] = table_columns

        result["study_types"] = result["study_type"]
        result["enrichment_tool"] = config.enrichment.enabled
        result["person_set_collections"] = person_set_collection_configs
        result["name"] = result["name"] or result["id"]

        result["enrichment"] = config.enrichment.to_dict()

        result["study_names"] = None
        if result["studies"] is not None:
            logger.debug(f"found studies in {config.id}")
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

    @abstractmethod
    def query_variants_wdae(self, kwargs, sources, max_variants_count=10000):
        pass


class StudyWrapper(StudyWrapperBase):
    def __init__(self, genotype_data_study, pheno_db, gene_weights_db):

        assert genotype_data_study is not None

        super().__init__(genotype_data_study)

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

    def get_studies_ids(self, leaves=True):
        return self.genotype_data_study.get_studies_ids(leaves=leaves)

    def _init_wdae_config(self):
        genotype_browser_config = self.config.genotype_browser
        if not genotype_browser_config:
            return

        # PERSON AND FAMILY FILTERS
        self.person_filters = genotype_browser_config.person_filters or None
        self.family_filters = genotype_browser_config.family_filters or None

        # GENE WEIGHTS
        if genotype_browser_config.column_groups:
            self.gene_weight_column_sources = [
                genotype_browser_config.columns.genotype[slot].source
                for slot in (
                    genotype_browser_config.column_groups.weights.columns or []
                )
            ]
        else:
            self.gene_weight_column_sources = []

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

    # def _query_variants_rows_iterator(
    #         self, sources, person_set_collection, **kwargs):

    #     if not kwargs.get("summaryVariantIds"):
    #         def filter_allele(allele):
    #             return True
    #     else:
    #         summary_variant_ids = set(kwargs.get("summaryVariantIds"))
    #         # logger.debug(f"sumamry variants ids: {summary_variant_ids}")

    #         def filter_allele(allele):
    #             svid = f"{allele.cshl_location}:{allele.cshl_variant}"
    #             return svid in summary_variant_ids

    #     variants = self.query_variants(**kwargs)

    #     for v in variants:
    #         matched = True
    #         for aa in v.matched_alleles:
    #             assert not aa.is_reference_allele
    #             if not filter_allele(aa):
    #                 matched = False
    #                 break
    #         if not matched:
    #             continue

    #         row_variant = self.response_transformer._build_variant_row(
    #             v, sources, person_set_collection=person_set_collection
    #         )

    #         yield row_variant

    @property
    def config_columns(self):
        return self.config.genotype_browser.columns

    def query_variants_wdae(
        self, kwargs, sources, max_variants_count=10000,
        max_variants_message=False
    ):
        people_group = kwargs.pop("peopleGroup", {})
        logger.debug(f"people group requested: {people_group}")
        if people_group:
            people_group = people_group.get("id")
        else:
            people_group = None
            selected_person_set_collections = self.genotype_data\
                .config\
                .person_set_collections\
                .selected_person_set_collections
            if selected_person_set_collections:
                people_group = selected_person_set_collections[0]

        logger.debug(f"people group selected: {people_group}")
        person_set_collection = self.get_person_set_collection(people_group)

        max_variants_count = kwargs.pop("maxVariantsCount", max_variants_count)
        summary_variant_ids = set(kwargs.pop("summaryVariantIds", []))

        kwargs = self.query_transformer.transform_kwargs(**kwargs)

        if not summary_variant_ids:
            def filter_allele(allele):
                return True
        else:
            def filter_allele(allele):
                svid = f"{allele.cshl_location}:{allele.cshl_variant}"
                return svid in summary_variant_ids

        transform = self.response_transformer.variant_transformer()

        try:
            variants = self.genotype_data_study.query_variants(**kwargs)
            for index, variant in enumerate(variants):
                if max_variants_count and index >= max_variants_count:
                    if max_variants_message:
                        yield [
                            f"# limit of {max_variants_count} variants "
                            f"reached"
                        ]
                    break

                v = transform(variant)

                matched = True
                for aa in v.matched_alleles:
                    assert not aa.is_reference_allele
                    if not filter_allele(aa):
                        matched = False
                        break
                if not matched:
                    continue

                row_variant = self.response_transformer._build_variant_row(
                    v, sources, person_set_collection=person_set_collection)

                yield row_variant
        except GeneratorExit:
            variants.close()
            logger.info(f"study wrapper query variants for {self.name} closed")

    def get_gene_view_summary_variants(self, frequency_column, **kwargs):
        kwargs = self.query_transformer.transform_kwargs(**kwargs)
        limit = kwargs.pop("maxVariantsCount", None)
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

    # def query_variants(self, **kwargs):
    #     print(100*"=")
    #     print("kwargs:", kwargs)
    #     kwargs = self.query_transformer.transform_kwargs(**kwargs)
    #     print("kwargs after tranform:", kwargs)
    #     print(100*"=")

    #     logger.info(f"query filters after translation: {kwargs}")

    #     if not kwargs.get("summaryVariantIds"):
    #         def filter_allele(allele):
    #             return True
    #     else:
    #         summary_variant_ids = set(kwargs.get("summaryVariantIds"))
    #         # logger.debug(f"sumamry variants ids: {summary_variant_ids}")

    #         def filter_allele(allele):
    #             svid = f"{allele.cshl_location}:{allele.cshl_variant}"
    #             return svid in summary_variant_ids

    #     sources = kwargs.get("sources")
    #     person_set_collection = kwargs.pop("person_set_collection")

    #     transform = self.response_transformer.variant_transformer()

    #     try:
    #         variants = self.genotype_data_study.query_variants(**kwargs)
    #         for variant in variants:
    #             v = transform(variant)

    #             matched = True
    #             for aa in v.matched_alleles:
    #                 assert not aa.is_reference_allele
    #                 if not filter_allele(aa):
    #                     matched = False
    #                     break
    #             if not matched:
    #                 continue

    #             row_variant = self.response_transformer._build_variant_row(
    #                 v, sources, person_set_collection=person_set_collection)

    #             yield row_variant
    #     except GeneratorExit:
    #         variants.close()
    #         logger.info(
    #               f"study wrapper query variants for {self.name} closed")

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


class RemoteStudyWrapper(StudyWrapperBase):

    def __init__(self, remote_genotype_data):
        self.remote_genotype_data = remote_genotype_data
        self._remote_study_id = remote_genotype_data._remote_study_id
        self.rest_client = remote_genotype_data.rest_client

        super().__init__(remote_genotype_data)

        self.phenotype_data = None
        pheno_id = self.config.get("pheotype_data")
        if pheno_id:
            self.phenotype_data = RemotePhenotypeData(
                self.rest_client.prefix_remote_identifier(pheno_id),
                self._remote_study_id,
                self.rest_client
            )

        self.is_remote = True

        self._person_set_collections = None
        self._person_set_collection_configs = None

        self.response_transformer = ResponseTransformer(self)

    @property
    def is_group(self):
        self.remote_genotype_data.is_group

    @property
    def config_columns(self):
        return self.config.genotype_browser.columns

    @property
    def families(self):
        return self.remote_genotype_data._families

    def get_studies_ids(self, leaves=True):
        return self.remote_genotype_data.get_studies_ids(leaves=leaves)

    def query_variants_wdae(
            self, kwargs, sources,
            max_variants_count=10000,
            max_variants_message=False):
        study_filters = kwargs.get("study_filters")
        people_group = kwargs.get("peopleGroup", {})

        if people_group:
            people_group = people_group.get("id")
        else:
            people_group = None
            selected_person_set_collections = self.genotype_data\
                .config\
                .person_set_collections\
                .selected_person_set_collections
            if selected_person_set_collections:
                people_group = selected_person_set_collections[0]
        person_set_collection = self.get_person_set_collection(people_group)

        if study_filters is not None:
            del kwargs["study_filters"]
        if kwargs.get("allowed_studies"):
            del kwargs["allowed_studies"]

        kwargs["datasetId"] = self._remote_study_id
        kwargs["maxVariantsCount"] = max_variants_count
        new_sources = []
        for qs in QUERY_SOURCES:
            if not any([qs["source"] == s["source"] for s in sources]):
                new_sources.append(qs)
        sources.extend(new_sources)
        for source in sources:
            if "format" in source:
                del source["format"]
        kwargs["sources"] = sources

        fam_id_idx = -1
        for idx, s in enumerate(sources):
            if s["source"] == "family":
                fam_id_idx = idx
                break

        assert fam_id_idx >= 0, fam_id_idx

        response = self.rest_client.post_query_variants(
            kwargs, reduceAlleles=False
        )

        def get_source(col):
            res = col['source']
            if 'role' in col:
                res = f"{res}.{col['role']}"
            return res

        for variant in response:
            fam_id = variant[fam_id_idx][0]
            family = self.families.get(fam_id)
            fv = RemoteFamilyVariant(
                variant, family, list(map(get_source, sources))
            )

            row_variant = self.response_transformer._build_variant_row(
                fv, sources, person_set_collection=person_set_collection
            )

            yield row_variant

    def get_person_set_collection(self, person_set_collection_id):
        return self.remote_genotype_data.get_person_set_collection(
            person_set_collection_id
        )
