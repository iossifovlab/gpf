import itertools
import json
import logging

from abc import abstractmethod

from box import Box

from dae.utils.dae_utils import join_line

from dae.variants.attributes import Role

from dae.studies.study import GenotypeData

from dae.configuration.gpf_config_parser import GPFConfigParser, FrozenBox
from remote.remote_phenotype_data import RemotePhenotypeData

from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer


logger = logging.getLogger(__name__)


class StudyWrapperBase(GenotypeData):

    def __init__(self, config):
        super(StudyWrapperBase, self).__init__(config, config.get("studies"))

    @abstractmethod
    def get_wdae_preview_info(self, query, max_variants_count=10000):
        pass

    @abstractmethod
    def get_variants_wdae_preview(self, query, max_variants_count=10000):
        pass

    @abstractmethod
    def get_variants_wdae_download(self, query, max_variants_count=10000):
        pass

    @abstractmethod
    def get_summary_variants_wdae_preview(
            self, query, max_variants_count=10000):
        pass

    @abstractmethod
    def get_summary_variants_wdae_download(
            self, query, max_variants_count=10000):
        pass

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

        # PHENO
        pheno_column_slots = []
        if genotype_browser_config.pheno:
            for col_id, pheno_col in genotype_browser_config.pheno.items():
                for slot in pheno_col.slots:
                    slot = GPFConfigParser.modify_tuple(
                        slot, {"id": f"{col_id}.{slot.name}"}
                    )
                    pheno_column_slots.append(slot)
        self.pheno_column_slots = pheno_column_slots or []

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
        self.legend = {}

        collections_conf = self.config.person_set_collections
        if collections_conf and \
                collections_conf.selected_person_set_collections:
            for collection_id in \
                    collections_conf.selected_person_set_collections:
                self.legend[collection_id] = \
                    self.person_set_collection_configs[collection_id]["domain"]

        # PREVIEW AND DOWNLOAD COLUMNS
        self._init_genotype_columns(genotype_browser_config)

    def _init_genotype_columns(self, genotype_browser_config):
        preview_column_names = genotype_browser_config.preview_columns
        download_column_names = \
            genotype_browser_config.download_columns \
            + (genotype_browser_config.selected_pheno_column_values or tuple())
        summary_preview_column_names = \
            genotype_browser_config.summary_preview_columns
        summary_download_column_names = \
            genotype_browser_config.summary_download_columns

        def unpack_columns(selected_columns, use_id=True):
            columns = []
            descs = []

            def inner(cols, get_source, use_id):
                cols_dict = cols

                for col_id in selected_columns:
                    col = cols_dict.get(col_id, None)

                    if not col:
                        continue
                    col = col.to_dict()
                    col["id"] = col_id

                    if col.get("source") is not None:
                        columns.append(col_id if use_id else col["name"])
                        col["source"] = get_source(col)
                        descs.append(col)

                    elif col.get("slots") is not None:
                        for slot in col.get("slots"):
                            scol_id = f"{col_id}.{slot['name']}" if use_id \
                                else f"{slot['name']}"

                            scol = slot.to_dict()
                            scol["id"] = scol_id
                            scol["source"] = get_source(slot)

                            columns.append(scol_id)
                            descs.append(scol)

            inner(
                genotype_browser_config.genotype,
                lambda x: f"{x['source']}",
                use_id
            )
            if genotype_browser_config.pheno:
                inner(
                    genotype_browser_config.pheno,
                    lambda x: f"{x['source']}.{x['role']}",
                    True
                )
            return columns, descs

        if genotype_browser_config.genotype:
            self.preview_columns, self.preview_descs = \
                unpack_columns(preview_column_names)

            self.download_columns, self.download_descs = unpack_columns(
                download_column_names, use_id=False
            )
            if summary_preview_column_names and \
                    len(summary_preview_column_names):
                self.summary_preview_columns, self.summary_preview_descs = \
                    unpack_columns(
                        summary_preview_column_names
                    )
                self.summary_download_columns, self.summary_download_descs = \
                    unpack_columns(
                        summary_download_column_names, use_id=False
                    )
            else:
                self.summary_preview_columns = []
                self.summary_preview_descs = []
                self.summary_download_columns = []
                self.summary_download_descs = []

        else:
            self.preview_columns, self.preview_descs = [], []
            self.download_columns, self.download_descs = [], []
            self.summary_preview_columns, self.summary_preview_descs = \
                [], []
            self.summary_download_columns, self.summary_download_descs = \
                [], []

    def _init_pheno(self, pheno_db):
        self.phenotype_data = None
        if self.config.phenotype_data:
            self.phenotype_data = pheno_db.get_phenotype_data(
                self.config.phenotype_data
            )

    def __getattr__(self, name):
        return getattr(self.genotype_data_study, name)

    def _query_variants_rows_iterator(
            self, sources, person_set_collection, **kwargs):

        if not kwargs.get("summaryVariantIds"):
            def filter_allele(allele):
                return True
        else:
            summary_variant_ids = set(kwargs.get("summaryVariantIds"))
            logger.debug(f"sumamry variants ids: {summary_variant_ids}")

            def filter_allele(allele):
                svid = f"{allele.cshl_location}:{allele.cshl_variant}"
                return svid in summary_variant_ids

        for v in self.query_variants(**kwargs):
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

    def get_variant_web_rows(self, query, sources, max_variants_count=10000):
        person_set_collection_id = query.get("peopleGroup", {}).get(
            "id", list(self.legend.keys())[0] if self.legend else None
        )
        person_set_collection = self.get_person_set_collection(
            person_set_collection_id
        )

        # if max_variants_count is not None:
        #     query["limit"] = max_variants_count

        rows_iterator = self._query_variants_rows_iterator(
            sources, person_set_collection, **query
        )

        if max_variants_count is not None:
            limited_rows = itertools.islice(rows_iterator, max_variants_count)
        else:
            limited_rows = rows_iterator

        return limited_rows

    def get_wdae_preview_info(self, query, max_variants_count=10000):
        preview_info = {}

        preview_info["cols"] = self.preview_columns
        preview_info["legend"] = self.get_legend(**query)

        preview_info["maxVariantsCount"] = max_variants_count

        return preview_info

    def get_variants_wdae_preview(self, query, max_variants_count=10000):
        variants_data = self.get_variant_web_rows(
            query,
            self.preview_descs,
            max_variants_count=max_variants_count,
        )

        return variants_data

    def get_variants_wdae_download(self, query, max_variants_count=10000):
        rows = self.get_variant_web_rows(
            query, self.download_descs, max_variants_count=max_variants_count
        )

        wdae_download = map(
            join_line, itertools.chain([self.download_columns], rows)
        )

        return wdae_download

    def get_summary_wdae_preview_info(self, query, max_variants_count=10000):
        preview_info = {}

        preview_info["cols"] = self.summary_preview_columns
        preview_info["legend"] = self.get_legend(**query)

        preview_info["maxVariantsCount"] = max_variants_count

        return preview_info

    def get_summary_variants_wdae_preview(
            self, query, max_variants_count=10000):
        if not self.summary_preview_columns:
            raise Exception("No summary preview columns specified")
        query["limit"] = max_variants_count
        rows = self.query_summary_variants(**query)
        return rows

    def get_summary_variants_wdae_download(
            self, query, max_variants_count=10000):
        if not self.summary_download_columns:
            raise Exception("No summary download columns specified")
        query["limit"] = max_variants_count
        rows = self.query_summary_variants(**query)

        wdae_download = map(
            join_line, itertools.chain([self.summary_download_columns], rows)
        )

        return wdae_download

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
        variants_from_studies = itertools.islice(
            self.genotype_data_study.query_variants(**kwargs), limit
        )
        for variant in self.response_transformer.transform_variants(
            variants_from_studies
        ):
            yield variant

    def query_summary_variants(self, **kwargs):
        kwargs = self.query_transformer.transform_kwargs(**kwargs)
        limit = None
        if "limit" in kwargs:
            limit = kwargs["limit"]
        logger.info(f"query filters after translation: {kwargs}")
        variants_from_studies = itertools.islice(
            self.genotype_data_study.query_summary_variants(**kwargs), limit
        )
        for variant in self.response_transformer.transform_summary_variants(
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

    def _get_legend_default_values(self):
        return [
            {
                "color": "#E0E0E0",
                "id": "missing-person",
                "name": "missing-person",
            }
        ]

    def get_legend(self, *args, **kwargs):
        if "peopleGroup" not in kwargs:
            legend = list(self.legend.values())[0] if self.legend else []
        else:
            legend = self.legend.get(kwargs["peopleGroup"]["id"], [])
        return legend + self._get_legend_default_values()

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
        ]
        result = {
            key: self.config.get(key, None) for key in keys
        }

        result["description"] = self.description

        bs_config = Box(self.config.genotype_browser)

        bs_config["columns"] = dict()
        for column in bs_config["preview_columns"]:
            if "pheno" in bs_config:
                assert (
                    column in bs_config["genotype"]
                    or column in bs_config["pheno"]
                ), column
                bs_config["columns"][column] = (
                    bs_config["genotype"].get(column, None)
                    or bs_config["pheno"][column]
                )
            else:
                assert column in bs_config["genotype"], column
                bs_config["columns"][column] = bs_config["genotype"][column]

        result["genotype_browser_config"] = bs_config
        result["genotype_browser"] = self.config.genotype_browser.enabled

        result["gene_browser"] = self.config.gene_browser

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
        config["id"] = self.rest_client.get_remote_dataset_id(study_id)
        config["name"] = f"({rest_client.remote_id}) {config['name']}"
        del config["access_rights"]
        del config["groups"]
        if config["parents"]:
            config["parents"] = list(
                map(
                    self.rest_client.get_remote_dataset_id,
                    config["parents"]
                )
            )

        if config.get("studies"):
            config["studies"] = list(
                map(
                    self.rest_client.get_remote_dataset_id,
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

    def get_wdae_preview_info(self, query, max_variants_count=10000):
        query["datasetId"] = self._remote_study_id
        return self.rest_client.get_browser_preview_info(query)

    def get_variants_wdae_preview(self, query, max_variants_count=10000):

        study_filters = query.get("study_filters")
        logger.debug(
            f"study_id: {self.study_id}; study_filters: {study_filters}")
        if study_filters is not None:
            del query["study_filters"]
        if query.get("allowed_studies"):
            del query["allowed_studies"]

            # if self.study_id not in study_filters:
            #     return
            # else:
            #     del query["study_filters"]

        query["datasetId"] = self._remote_study_id
        query["maxVariantsCount"] = max_variants_count
        print("query:", query)

        response = self.rest_client.get_variants_preview(query)
        for line in response.iter_lines():
            if line:
                variants = json.loads(line)
                for variant in variants:
                    yield variant

    def get_variants_wdae_download(self, query, max_variants_count=10000):
        raise NotImplementedError

    def get_summary_variants_wdae_preview(
            self, query, max_variants_count=10000):
        raise NotImplementedError

    def get_summary_variants_wdae_download(
            self, query, max_variants_count=10000):
        raise NotImplementedError

    def build_genotype_data_group_description(self, gpf_instance):
        return self.config.to_dict()
