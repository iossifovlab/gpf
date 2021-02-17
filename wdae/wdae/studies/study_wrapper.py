import itertools
import traceback
import json
import logging

from typing import List, Dict

from abc import abstractmethod

from box import Box

from dae.utils.variant_utils import mat2str, fgt2str
from dae.utils.dae_utils import split_iterable, join_line

from dae.utils.effect_utils import ge2str, \
    gd2str, \
    gene_effect_get_worst_effect, \
    gene_effect_get_genes

from dae.variants.attributes import Role, Inheritance, VariantDesc
from dae.variants.family_variant import FamilyVariant

from dae.studies.study import GenotypeData

from dae.configuration.gpf_config_parser import GPFConfigParser, FrozenBox
from dae.person_sets import PersonSetCollection
from remote.remote_phenotype_data import RemotePhenotypeData

from studies.query_transformer import QueryTransformer


logger = logging.getLogger(__name__)


def members_in_order_get_family_structure(mio):
    return ";".join([
        f"{p.role.name}:{p.sex.short()}:{p.status.name}" for p in mio])


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

    SPECIAL_ATTRS = {
        "family":
        lambda v: [v.family_id],

        "location":
        lambda v: v.cshl_location,

        "variant":
        lambda v: VariantDesc.combine([
            aa.details.variant_desc for aa in v.alt_alleles]),

        "position":
        lambda v: [aa.position for aa in v.alt_alleles],

        "reference":
        lambda v: [aa.reference for aa in v.alt_alleles],

        "alternative":
        lambda v: [aa.alternative for aa in v.alt_alleles],

        "genotype":
        lambda v: [fgt2str(v.family_genotype)],

        "best_st":
        lambda v: [mat2str(v.family_best_state)],

        "family_structure":
        lambda v: [members_in_order_get_family_structure(
            v.members_in_order)],

        "family_person_ids": 
        lambda v: [";".join(list(map(
            lambda m: m.person_id, v.members_in_order
        )))],

        "carrier_person_ids":
        lambda v: list(
            map(
                lambda aa: ";".join(list(filter(None, aa.variant_in_members))),
                v.alt_alleles
            )),

        "carrier_person_attributes": 
        lambda v: list(
            map(
                lambda aa: members_in_order_get_family_structure(
                    filter(None, aa.variant_in_members_objects)
                ),
                v.alt_alleles
            )),

        "inheritance_type":
        lambda v: list(
            map(
                lambda aa:
                "denovo"
                if Inheritance.denovo in aa.inheritance_in_members
                else "mendelian"
                if Inheritance.mendelian in aa.inheritance_in_members
                else "-",
                v.alt_alleles)
        ),

        "is_denovo":
        lambda v: list(
            map(
                lambda aa:
                Inheritance.denovo in aa.inheritance_in_members,
                v.alt_alleles)
        ),

        "effects":
        lambda v: [ge2str(e) for e in v.effects],

        "genes":
        lambda v: [gene_effect_get_genes(e) for e in v.effects],

        "worst_effect":
        lambda v: [gene_effect_get_worst_effect(e) for e in v.effects],

        "effect_details":
        lambda v: [gd2str(e) for e in v.effects],

        "seen_in_affected":
        lambda v: bool(v.get_attribute("seen_in_status") in {2, 3}),

        "seen_in_unaffected":
        lambda v: bool(v.get_attribute("seen_in_status") in {1, 3}),

    }

    PHENOTYPE_ATTRS = {
        "family_phenotypes":
        lambda v, phenotype_person_sets:
        [
            ':'.join([
                phenotype_person_sets.get_person_set_of_person(mid).name
                for mid in v.members_ids])
        ],

        "carrier_phenotypes":
        lambda v, phenotype_person_sets:
        [':'.join([
            phenotype_person_sets.get_person_set_of_person(mid).name
            for mid in filter(None, aa.variant_in_members)])
         for aa in v.alt_alleles],
    }

    def generate_pedigree(self, variant, person_set_collection):
        result = []
        # best_st = np.sum(allele.gt == allele.allele_index, axis=0)
        genotype = variant.family_genotype

        missing_members = set()
        for index, member in enumerate(variant.members_in_order):
            try:
                result.append(
                    self._get_wdae_member(
                        member, person_set_collection,
                        "/".join([
                            str(v) for v in filter(
                                lambda g: g != 0, genotype[index]
                            )]
                        )
                    )
                )
            except IndexError:
                import traceback
                traceback.print_exc()
                missing_members.add(member.person_id)
                logger.error(f"{genotype}, {index}, {member}")

        for member in variant.family.full_members:
            if (member.generated or member.not_sequenced) \
                    or (member.person_id in missing_members):
                result.append(
                    self._get_wdae_member(member, person_set_collection, 0)
                )

        return result

    def _build_variant_row(
            self, v: FamilyVariant, column_descs: List[Dict], **kwargs):

        row_variant = []
        for col_desc in column_descs:
            try:
                col_source = col_desc["source"]
                col_format = col_desc.get("format")

                if col_format is None:
                    def col_formatter(val):
                        if val is None:
                            return "-"
                        else:
                            return str(val)
                else:
                    def col_formatter(val):
                        if val is None:
                            return "-"
                        try:
                            return col_format % val
                        except Exception:
                            logging.exception(f'error build variant: {v}')
                            traceback.print_stack()
                            return "-"

                if col_source == "pedigree":
                    person_set_collection = \
                        kwargs.get("person_set_collection")
                    row_variant.append(
                        self.generate_pedigree(
                            v, person_set_collection
                        )
                    )
                elif col_source in self.PHENOTYPE_ATTRS:
                    phenotype_person_sets = \
                        self.person_set_collections.get("phenotype")
                    if phenotype_person_sets is None:
                        row_variant.append("-")
                    fn = self.PHENOTYPE_ATTRS[col_source]
                    row_variant.append(
                        ",".join(fn(v, phenotype_person_sets)))

                elif col_source == "study_phenotype":
                    row_variant.append(self.config.study_phenotype)

                else:
                    if col_source in self.SPECIAL_ATTRS:
                        attribute = self.SPECIAL_ATTRS[col_source](v)
                    else:
                        attribute = v.get_attribute(col_source)

                    if all([a == attribute[0] for a in attribute]):
                        attribute = [attribute[0]]
                    attribute = list(map(col_formatter, attribute))

                    row_variant.append(",".join([str(a) for a in attribute]))

            except (AttributeError, KeyError, Exception):
                logging.exception(f'error build variant: {v}')
                traceback.print_stack()
                row_variant.append([""])
                raise

        return row_variant

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
            row_variant = self._build_variant_row(
                v, sources, person_set_collection=person_set_collection)

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
            for a in v.alt_alleles:
                yield {
                    "location": a.cshl_location,
                    "position": a.position,
                    "end_position": a.end_position,
                    "chrom": a.chrom,
                    "frequency": a.get_attribute(frequency_column),
                    "effect": gene_effect_get_worst_effect(a.effect),
                    "variant": a.cshl_variant,
                    "family_variants_count":
                        a.get_attribute("family_variants_count"),
                    "is_denovo": a.get_attribute("seen_as_denovo"),
                    "seen_in_affected":
                        a.get_attribute("seen_in_status") in {2, 3},
                    "seen_in_unaffected":
                        a.get_attribute("seen_in_status") in {1, 3},
                }

    def get_gene_view_summary_variants_download(
            self, frequency_column, **kwargs):
        kwargs = self.query_transformer.transform_kwargs(**kwargs)
        limit = None
        if "limit" in kwargs:
            limit = kwargs["limit"]

        variants_from_studies = itertools.islice(
            self.genotype_data_study.query_summary_variants(**kwargs), limit
        )

        columns = [
            "location",
            "position",
            "end_position",
            "chrom",
            "frequency",
            "effect",
            "variant",
            "family_variants_count",
            "is_denovo",
            "seen_in_affected",
            "seen_in_unaffected"
        ]

        def variants_iterator(variants):
            for v in variants:
                for a in v.alt_alleles:
                    yield [
                        a.cshl_location,
                        a.position,
                        a.end_position,
                        a.chrom,
                        a.get_attribute(frequency_column),
                        gene_effect_get_worst_effect(a.effect),
                        a.cshl_variant,
                        a.get_attribute("family_variants_count"),
                        a.get_attribute("seen_as_denovo"),
                        a.get_attribute("seen_in_status") in {2, 3},
                        a.get_attribute("seen_in_status") in {1, 3},
                    ]

        rows = variants_iterator(variants_from_studies)
        return map(join_line, itertools.chain([columns], rows))

    def query_variants(self, **kwargs):
        kwargs = self.query_transformer.transform_kwargs(**kwargs)
        limit = None
        if "limit" in kwargs:
            limit = kwargs["limit"]
        logger.info(f"query filters after translation: {kwargs}")
        variants_from_studies = itertools.islice(
            self.genotype_data_study.query_variants(**kwargs), limit
        )
        for variant in self._add_additional_columns(variants_from_studies):
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
        variants_with_additional_cols = self._add_additional_columns_summary(
            variants_from_studies)
        for v in variants_with_additional_cols:
            row_variant = self._build_variant_row(
                v, self.summary_preview_descs)

            yield row_variant

    STREAMING_CHUNK_SIZE = 20

    def _add_additional_columns(self, variants_iterable):
        for variants_chunk in split_iterable(
                variants_iterable, self.STREAMING_CHUNK_SIZE):

            families = {variant.family_id for variant in variants_chunk}

            pheno_column_values = self._get_all_pheno_values(families)

            for variant in variants_chunk:
                pheno_values = self._get_pheno_values_for_variant(
                    variant, pheno_column_values
                )

                for allele in variant.alt_alleles:
                    gene_weights_values = self._get_gene_weights_values(allele)
                    allele.update_attributes(gene_weights_values)

                    if pheno_values:
                        allele.update_attributes(pheno_values)

                yield variant

    def _add_additional_columns_summary(self, variants_iterable):
        for variants_chunk in split_iterable(
                variants_iterable, self.STREAMING_CHUNK_SIZE):

            for variant in variants_chunk:
                for allele in variant.alt_alleles:
                    gene_weights_values = self._get_gene_weights_values(allele)

                    allele.update_attributes(gene_weights_values)

                yield variant

    def _get_pheno_values_for_variant(self, variant, pheno_column_values):
        if not pheno_column_values:
            return None

        pheno_values = {}

        for pheno_column_df, pheno_column_name in pheno_column_values:
            variant_pheno_value_df = pheno_column_df[
                pheno_column_df["person_id"].isin(variant.members_ids)
            ]
            variant_pheno_value_df.set_index("person_id", inplace=True)
            assert len(variant_pheno_value_df.columns) == 1
            column = variant_pheno_value_df.columns[0]

            pheno_values[pheno_column_name] = ",".join(
                variant_pheno_value_df[column].map(str).tolist()
            )

        return pheno_values

    def _get_all_pheno_values(self, family_ids):
        if not self.phenotype_data or not self.pheno_column_slots:
            return None

        pheno_column_names = []
        pheno_column_dfs = []
        for slot in self.pheno_column_slots:
            assert slot.role
            persons = self.families.persons_with_roles(
                [slot.role], family_ids)
            person_ids = [p.person_id for p in persons]

            kwargs = {
                "person_ids": list(person_ids),
            }

            pheno_column_names.append(f"{slot.source}.{slot.role}")
            pheno_column_dfs.append(
                self.phenotype_data.get_measure_values_df(
                    slot.source, **kwargs
                )
            )

        result = list(zip(pheno_column_dfs, pheno_column_names))
        return result

    def _get_gene_weights_values(self, allele, default=None):
        if not self.gene_weight_column_sources:
            return {}
        genes = gene_effect_get_genes(allele.effects).split(";")
        gene = genes[0]

        gene_weights_values = {}
        for gwc in self.gene_weight_column_sources:
            if gwc not in self.gene_weights_db:
                continue

            gene_weights = self.gene_weights_db[gwc]
            if gene != "":
                gene_weights_values[gwc] = gene_weights._to_dict().get(
                    gene, default
                )
            else:
                gene_weights_values[gwc] = default

        return gene_weights_values

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

    def _get_wdae_member(self, member, person_set_collection, best_st):
        return [
            member.family_id,
            member.person_id,
            member.mom_id if member.mom_id else "0",
            member.dad_id if member.dad_id else "0",
            member.sex.short(),
            str(member.role),
            PersonSetCollection.get_person_color(
                member, person_set_collection
            ),
            member.layout,
            (member.generated or member.not_sequenced),
            best_st,
            0,
        ]


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
