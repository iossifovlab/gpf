import math
import itertools
import traceback
import json
import logging

from typing import List, Set

from functools import reduce

from box import Box

from dae.utils.variant_utils import mat2str
from dae.utils.dae_utils import (
    split_iterable,
    join_line,
    members_in_order_get_family_structure,
)
from dae.utils.effect_utils import (
    expand_effect_types,
    ge2str,
    gd2str,
    gene_effect_get_worst_effect,
    gene_effect_get_genes,
)

from dae.utils.regions import Region
from dae.pheno_tool.pheno_common import PhenoFilterBuilder
from dae.variants.attributes import Role, Inheritance

from dae.backends.attributes_query import (
    role_query,
    variant_type_converter,
    sex_converter,
    AndNode,
    NotNode,
    OrNode,
    ContainsNode,
)
from dae.studies.study import GenotypeDataGroup

from dae.configuration.gpf_config_parser import GPFConfigParser, FrozenBox
from dae.person_sets import PersonSetCollection
from remote.remote_phenotype_data import RemotePhenotypeData


logger = logging.getLogger(__name__)


class StudyWrapperBase:
    def get_wdae_preview_info(self, query, max_variants_count=10000):
        raise NotImplementedError

    def get_variants_wdae_preview(self, query, max_variants_count=10000):
        raise NotImplementedError

    def get_variants_wdae_download(self, query, max_variants_count=10000):
        raise NotImplementedError

    def get_wdae_summary_preview_info(self, query, max_variants_count=10000):
        raise NotImplementedError

    def get_summary_variants_wdae_preview(
            self, query, max_variants_count=10000):
        raise NotImplementedError

    def get_summary_variants_wdae_download(
            self, query, max_variants_count=10000):
        raise NotImplementedError

    def build_genotype_data_group_description(self, gpf_instance):
        raise NotImplementedError


class StudyWrapper(StudyWrapperBase):
    def __init__(
        self, genotype_data_study, pheno_db, gene_weights_db
    ):
        assert genotype_data_study is not None

        self.genotype_data_study = genotype_data_study
        self.is_group = isinstance(genotype_data_study, GenotypeDataGroup)
        self.config = genotype_data_study.config
        assert self.config is not None

        self.is_remote = False

        self._init_wdae_config()
        self.pheno_db = pheno_db
        self._init_pheno(self.pheno_db)

        self.gene_weights_db = gene_weights_db

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

        # IN ROLE
        self.in_role_columns = genotype_browser_config.in_roles or []

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
        preview_column_names = genotype_browser_config.preview_columns
        download_column_names = \
            genotype_browser_config.download_columns \
            + (genotype_browser_config.selected_pheno_column_values or tuple())
        summary_preview_column_names = \
            genotype_browser_config.summary_preview_columns
        summary_download_column_names = \
            genotype_browser_config.summary_download_columns

        def unpack_columns(selected_columns, use_id=True):
            columns, sources = [], []

            def inner(cols, get_source, use_id):
                cols_dict = cols

                for col_id in selected_columns:
                    col = cols_dict.get(col_id, None)
                    if not col:
                        continue
                    if col.source is not None:
                        columns.append(col_id if use_id else col.name)
                        sources.append(get_source(col))
                    if col.slots is not None:
                        for slot in col.slots:
                            columns.append(
                                f"{col_id}.{slot.name}"
                                if use_id
                                else f"{slot.name}"
                            )
                            sources.append(get_source(slot))

            inner(
                genotype_browser_config.genotype,
                lambda x: f"{x.source}",
                use_id
            )
            if genotype_browser_config.pheno:
                inner(
                    genotype_browser_config.pheno,
                    lambda x: f"{x.source}.{x.role}",
                    True
                )
            return columns, sources

        if genotype_browser_config.genotype:
            self.preview_columns, self.preview_sources = unpack_columns(
                preview_column_names
            )
            self.download_columns, self.download_sources = unpack_columns(
                download_column_names, use_id=False
            )
            if summary_preview_column_names and \
                    len(summary_preview_column_names):
                self.summary_preview_columns, self.summary_preview_sources = \
                    unpack_columns(
                        summary_preview_column_names
                    )
                self.summary_download_columns, self.summary_download_sources =\
                    unpack_columns(
                        summary_download_column_names, use_id=False
                    )
            else:
                self.summary_preview_columns = None
                self.summary_preview_sources = None
                self.summary_download_columns = None
                self.summary_download_sources = None

        else:
            self.preview_columns, self.preview_sources = [], []
            self.download_columns, self.download_sources = [], []
            self.summary_preview_columns, self.summary_preview_sources = [], []
            self.summary_download_columns, self.summary_download_sources = \
                [], []

    def _init_pheno(self, pheno_db):
        self.phenotype_data = None
        self.pheno_filter_builder = None
        if self.config.phenotype_data:
            self.phenotype_data = pheno_db.get_phenotype_data(
                self.config.phenotype_data
            )
            self.pheno_filter_builder = PhenoFilterBuilder(
                self.phenotype_data
            )

    def __getattr__(self, name):
        return getattr(self.genotype_data_study, name)

    FILTER_RENAMES_MAP = {
        "familyIds": "family_ids",
        "gender": "sexes",
        "geneSymbols": "genes",
        "variantTypes": "variant_type",
        "effectTypes": "effect_types",
        "regionS": "regions",
    }

    STANDARD_ATTRS = {
        "family": "family_id",
        "location": "cshl_location",
        "variant": "cshl_variant",
    }

    STANDARD_ATTRS_LAMBDAS = {
        key: lambda aa, val=val: getattr(aa, val)
        for key, val in STANDARD_ATTRS.items()
    }

    SPECIAL_ATTRS_FORMAT = {
        "genotype": lambda aa: mat2str(aa.genotype),
        "effects": lambda aa: ge2str(aa.effect),
        "genes": lambda aa: gene_effect_get_genes(aa.effect),
        "worst_effect": lambda aa: gene_effect_get_worst_effect(aa.effect),
        "effect_details": lambda aa: gd2str(aa.effect),
        "best_st": lambda aa: mat2str(aa.best_state),
        "family_structure": lambda aa: members_in_order_get_family_structure(
            aa.members_in_order
        ),
        "is_denovo": lambda aa: bool(
            Inheritance.denovo in aa.inheritance_in_members
        ),
        "seen_in_affected":
        lambda aa: bool(aa.get_attribute("seen_in_status") in {2, 3}),
        "seen_in_unaffected":
        lambda aa: bool(aa.get_attribute("seen_in_status") in {1, 3}),

    }

    SPECIAL_ATTRS = {**SPECIAL_ATTRS_FORMAT, **STANDARD_ATTRS_LAMBDAS}

    def generate_pedigree(self, allele, person_set_collection):
        result = []
        # best_st = np.sum(allele.gt == allele.allele_index, axis=0)
        best_st = allele.best_state[allele.allele_index, :]

        missing_members = set()
        for index, member in enumerate(allele.members_in_order):
            try:
                result.append(
                    self._get_wdae_member(
                        member, person_set_collection, int(best_st[index])
                    )
                )
            except IndexError:
                import traceback
                traceback.print_exc()
                missing_members.add(member.person_id)
                logger.error(f"{best_st}, {index}, {member}")

        for member in allele.family.full_members:
            if (member.generated or member.not_sequenced) \
                    or (member.person_id in missing_members):
                result.append(
                    self._get_wdae_member(member, person_set_collection, 0)
                )

        return result

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
            for aa in v.matched_alleles:
                assert not aa.is_reference_allele
                if not filter_allele(aa):
                    continue

                row_variant = []
                for source in sources:
                    try:
                        if source in self.SPECIAL_ATTRS:
                            row_variant.append(
                                self.SPECIAL_ATTRS[source](aa))
                        elif source == "pedigree":
                            row_variant.append(
                                self.generate_pedigree(
                                    aa, person_set_collection
                                )
                            )
                        else:
                            attribute = aa.get_attribute(source, "-")

                            if not isinstance(attribute, str) and \
                                    not isinstance(attribute, list):
                                if attribute is None or math.isnan(attribute):
                                    attribute = "-"
                                elif math.isinf(attribute):
                                    attribute = "inf"
                            if attribute == "":
                                attribute = "-"
                            row_variant.append(attribute)

                    except (AttributeError, KeyError):
                        traceback.print_exc()
                        row_variant.append("")

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
            self.preview_sources,
            max_variants_count=max_variants_count,
        )

        return variants_data

    def get_variants_wdae_download(self, query, max_variants_count=10000):
        rows = self.get_variant_web_rows(
            query, self.download_sources, max_variants_count=max_variants_count
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
        kwargs = self._transform_kwargs(**kwargs)
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
        kwargs = self._transform_kwargs(**kwargs)
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

    # Not implemented:
    # callSet
    # minParentsCalled
    # ultraRareOnly
    # TMM_ALL
    def _transform_kwargs(self, **kwargs):
        logger.debug(f"kwargs in study wrapper: {kwargs}")
        StudyWrapper._add_inheritance_to_query(
            "not possible_denovo and not possible_omission",
            kwargs
        )

        kwargs = self._add_people_with_people_group(kwargs)

        if "uniqueFamilyVariants" in kwargs:
            kwargs["unique_family_variants"] = kwargs["uniqueFamilyVariants"]
            del kwargs["uniqueFamilyVariants"]

        if "regions" in kwargs:
            kwargs["regions"] = list(map(Region.from_str, kwargs["regions"]))

        if "presentInChild" in kwargs or "presentInParent" in kwargs:
            self._transform_present_in_child_and_present_in_parent(kwargs)

        if "presentInRole" in kwargs:
            self._transform_present_in_role(kwargs)

        if (
            "minAltFrequencyPercent" in kwargs
            or "maxAltFrequencyPercent" in kwargs
        ):
            self._transform_min_max_alt_frequency(kwargs)

        if "genomicScores" in kwargs:
            self._transform_genomic_scores(kwargs)

        if "geneWeights" in kwargs:
            self._transform_gene_weights(kwargs)

        for key in list(kwargs.keys()):
            if key in self.FILTER_RENAMES_MAP:
                kwargs[self.FILTER_RENAMES_MAP[key]] = kwargs[key]
                kwargs.pop(key)

        if "sexes" in kwargs:
            sexes = set(kwargs["sexes"])
            if sexes != set(["female", "male", "unspecified"]):
                sexes = [ContainsNode(sex_converter(sex)) for sex in sexes]
                kwargs["sexes"] = OrNode(sexes)
            else:
                kwargs["sexes"] = None

        if "variant_type" in kwargs:
            variant_types = set(kwargs["variant_type"])

            if variant_types != {"ins", "del", "sub", "CNV"}:
                if "CNV" in variant_types:
                    variant_types.remove("CNV")
                    variant_types.add("CNV+")
                    variant_types.add("CNV-")

                variant_types = [
                    ContainsNode(variant_type_converter(t))
                    for t in variant_types
                ]
                kwargs["variant_type"] = OrNode(variant_types)
            else:
                del kwargs["variant_type"]

        if "effect_types" in kwargs:
            kwargs["effect_types"] = expand_effect_types(
                kwargs["effect_types"]
            )

        if "studyFilters" in kwargs:
            if kwargs["studyFilters"]:
                request = set([
                    sf["studyId"] for sf in kwargs["studyFilters"]
                ])
                study_filters = kwargs.get("study_filters")
                if study_filters is None:
                    kwargs["study_filters"] = request
                else:
                    kwargs["study_filters"] = request & set(study_filters)
            else:
                del kwargs["studyFilters"]

        if "personFilters" in kwargs:
            kwargs = self._transform_person_filters(kwargs)

        if "familyFilters" in kwargs:
            kwargs = self._transform_family_filters(kwargs)

        if "person_ids" in kwargs:
            kwargs["person_ids"] = list(kwargs["person_ids"])

        if "inheritanceTypeFilter" in kwargs:
            kwargs["inheritance"].append(
                "any({})".format(
                    ",".join(kwargs["inheritanceTypeFilter"])))
            kwargs.pop("inheritanceTypeFilter")
        if "affectedStatus" in kwargs:
            statuses = kwargs.pop("affectedStatus")
            kwargs["affected_status"] = [
                status.lower() for status in statuses
            ]
        return kwargs

    def query_variants(self, **kwargs):
        kwargs = self._transform_kwargs(**kwargs)
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
        kwargs = self._transform_kwargs(**kwargs)
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
            for aa in v.alt_alleles:
                assert not aa.is_reference_allele

                row_variant = []
                for source in self.summary_preview_sources:
                    try:
                        if source in self.SPECIAL_ATTRS:
                            row_variant.append(self.SPECIAL_ATTRS[source](aa))
                        elif source == "pedigree":
                            pass
                        else:
                            attribute = aa.get_attribute(source, "-")

                            if not isinstance(attribute, str) and \
                                    not isinstance(attribute, list):
                                if attribute is None or math.isnan(attribute):
                                    attribute = "-"
                                elif math.isinf(attribute):
                                    attribute = "inf"
                            if attribute == "":
                                attribute = "-"

                            row_variant.append(attribute)

                    except (AttributeError, KeyError):
                        traceback.print_exc()
                        row_variant.append("")

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
                    roles_values = self._get_all_roles_values(allele)
                    gene_weights_values = self._get_gene_weights_values(allele)

                    if pheno_values:
                        allele.update_attributes(pheno_values)

                    if roles_values:
                        allele.update_attributes(roles_values)

                    allele.update_attributes(gene_weights_values)

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

            pheno_values[pheno_column_name] = list(
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

    def _get_gene_weights_values(self, allele):
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
                    gene, ""
                )
            else:
                gene_weights_values[gwc] = ""

        return gene_weights_values

    def _get_all_roles_values(self, allele):
        if not self.in_role_columns:
            return None

        result = {}
        for roles_value in self.in_role_columns.values():
            result[roles_value.destination] = "".join(
                self._get_roles_value(allele, roles_value.roles)
            )

        return result

    def _get_roles_value(self, allele, roles):
        result = []
        variant_in_members = allele.variant_in_members_objects
        for role in roles:
            for member in variant_in_members:
                role = Role.from_name(role)
                if member.role == role:
                    result.append(str(role) + member.sex.short())

        return result

    def _add_people_with_people_group(self, kwargs):

        # TODO Rename peopleGroup kwarg to person_set_collections
        # and all other, relevant keys in the kwargs dict

        if kwargs.get("peopleGroup") is None:
            return kwargs

        person_set_collections_query = kwargs.pop("peopleGroup")
        person_set_collection_id = person_set_collections_query["id"]
        selected_person_set_ids = set(
            person_set_collections_query["checkedValues"]
        )

        person_set_collection = self.genotype_data_study \
            .get_person_set_collection(person_set_collection_id)

        if set(person_set_collection.person_sets.keys()) == \
                selected_person_set_ids:
            return kwargs

        person_set_collection_query = (
            person_set_collection_id, selected_person_set_ids
        )
        kwargs["person_set_collection"] = person_set_collection_query
        return kwargs

    def _transform_genomic_scores(self, kwargs):
        genomic_scores = kwargs.pop("genomicScores", [])

        genomic_scores_filter = [
            (score["metric"], (score["rangeStart"], score["rangeEnd"]))
            for score in genomic_scores
            # if score["rangeStart"] or score["rangeEnd"]
        ]

        if "real_attr_filter" not in kwargs:
            kwargs["real_attr_filter"] = []
        kwargs["real_attr_filter"] += genomic_scores_filter

    def _transform_gene_weights(self, kwargs):
        if not self.gene_weights_db:
            return

        gene_weights = kwargs.pop("geneWeights", {})

        weight_name = gene_weights.get("weight", None)
        range_start = gene_weights.get("rangeStart", None)
        range_end = gene_weights.get("rangeEnd", None)

        if weight_name and weight_name in self.gene_weights_db:
            weight = self.gene_weights_db[gene_weights.get("weight")]

            genes = weight.get_genes(range_start, range_end)

            if "genes" not in kwargs:
                kwargs["genes"] = []

            kwargs["genes"] += list(genes)

    def _transform_min_max_alt_frequency(self, kwargs):
        min_value = None
        max_value = None

        if "minAltFrequencyPercent" in kwargs:
            min_value = kwargs["minAltFrequencyPercent"]
            kwargs.pop("minAltFrequencyPercent")

        if "maxAltFrequencyPercent" in kwargs:
            max_value = kwargs["maxAltFrequencyPercent"]
            kwargs.pop("maxAltFrequencyPercent")

        value_range = (min_value, max_value)

        if value_range == (None, None):
            return

        if value_range[0] is None:
            value_range = (float("-inf"), value_range[1])

        if value_range[1] is None:
            value_range = (value_range[0], float("inf"))

        value = "af_allele_freq"
        if "real_attr_filter" not in kwargs:
            kwargs["real_attr_filter"] = []

        kwargs["real_attr_filter"].append((value, value_range))

    @staticmethod
    def _transform_present_in_child_and_present_in_parent(kwargs):
        if "presentInChild" in kwargs:
            present_in_child = set(kwargs["presentInChild"])
            kwargs.pop("presentInChild")
        else:
            present_in_child = set()

        if "presentInParent" in kwargs:
            present_in_parent = \
                set(kwargs["presentInParent"]["presentInParent"])
            rarity = kwargs["presentInParent"].get("rarity", None)
            kwargs.pop("presentInParent")
        else:
            present_in_parent = set()
            rarity = None

        roles_query = []
        roles_query.append(
            StudyWrapper._present_in_child_to_roles(present_in_child))
        roles_query.append(
            StudyWrapper._present_in_parent_to_roles(present_in_parent))
        roles_query = list(filter(lambda rq: rq is not None, roles_query))
        if len(roles_query) == 2:
            roles_query = AndNode(roles_query)
        elif len(roles_query) == 1:
            roles_query = roles_query[0]
        else:
            roles_query = None

        StudyWrapper._add_roles_to_query(roles_query, kwargs)

        inheritance = None
        if present_in_child == set(["neither"]) and \
                present_in_parent != set(["neither"]):
            inheritance = [Inheritance.mendelian, Inheritance.missing]
        elif present_in_child != set(["neither"]) and \
                present_in_parent == set(["neither"]):
            inheritance = [Inheritance.denovo]
        else:
            inheritance = [
                Inheritance.denovo,
                Inheritance.mendelian,
                Inheritance.missing]
        inheritance = [str(inh) for inh in inheritance]
        StudyWrapper._add_inheritance_to_query(
            "any({})".format(",".join(inheritance)), kwargs)

        if present_in_parent == {"neither"}:
            return

        if rarity is not None:
            ultra_rare = rarity.get("ultraRare", None)
            ultra_rare = bool(ultra_rare)
            if ultra_rare:
                kwargs["ultra_rare"] = True
            else:
                max_alt_freq = rarity.get("maxFreq", None)
                min_alt_freq = rarity.get("minFreq", None)
                if min_alt_freq is not None or max_alt_freq is not None:
                    frequency_filter = kwargs.get("frequency_filter", [])
                    frequency_filter.append(
                        ("af_allele_freq", (min_alt_freq, max_alt_freq))
                    )
                    kwargs["frequency_filter"] = frequency_filter

    @staticmethod
    def _present_in_child_to_roles(present_in_child):
        roles_query = []

        if "proband only" in present_in_child:
            roles_query.append(AndNode(
                [ContainsNode(Role.prb), NotNode(ContainsNode(Role.sib))]
            ))

        if "sibling only" in present_in_child:
            roles_query.append(AndNode(
                [NotNode(ContainsNode(Role.prb)), ContainsNode(Role.sib)]
            ))

        if "proband and sibling" in present_in_child:
            roles_query.append(AndNode(
                [ContainsNode(Role.prb), ContainsNode(Role.sib)]
            ))

        if "neither" in present_in_child:
            roles_query.append(AndNode(
                [
                    NotNode(ContainsNode(Role.prb)),
                    NotNode(ContainsNode(Role.sib)),
                ]
            ))
        if len(roles_query) == 4 or len(roles_query) == 0:
            return None
        if len(roles_query) == 1:
            return roles_query[0]
        return OrNode(roles_query)

    @staticmethod
    def _present_in_parent_to_roles(present_in_parent):
        roles_query = []

        if "mother only" in present_in_parent:
            roles_query.append(AndNode(
                [
                    NotNode(ContainsNode(Role.dad)),
                    ContainsNode(Role.mom),
                ]
            ))

        if "father only" in present_in_parent:
            roles_query.append(AndNode(
                [
                    ContainsNode(Role.dad),
                    NotNode(ContainsNode(Role.mom)),
                ]
            ))

        if "mother and father" in present_in_parent:
            roles_query.append(AndNode(
                [ContainsNode(Role.dad), ContainsNode(Role.mom)]
            ))

        if "neither" in present_in_parent:
            roles_query.append(AndNode(
                [
                    NotNode(ContainsNode(Role.dad)),
                    NotNode(ContainsNode(Role.mom)),
                ]
            ))
        if len(roles_query) == 4 or len(roles_query) == 0:
            return None
        if len(roles_query) == 1:
            return roles_query[0]
        return OrNode(roles_query)

    @staticmethod
    def _transform_present_in_parent(kwargs):
        roles_query = []
        present_in_parent = set(kwargs["presentInParent"]["presentInParent"])
        rarity = kwargs["presentInParent"].get("rarity", None)

        if present_in_parent != set(
            ["father only", "mother only", "mother and father", "neither"]
        ):

            for filter_option in present_in_parent:
                new_roles = None

                if filter_option == "mother only":
                    new_roles = AndNode(
                        [
                            NotNode(ContainsNode(Role.dad)),
                            ContainsNode(Role.mom),
                        ]
                    )

                if filter_option == "father only":
                    new_roles = AndNode(
                        [
                            ContainsNode(Role.dad),
                            NotNode(ContainsNode(Role.mom)),
                        ]
                    )

                if filter_option == "mother and father":
                    new_roles = AndNode(
                        [ContainsNode(Role.dad), ContainsNode(Role.mom)]
                    )

                if filter_option == "neither":
                    new_roles = AndNode(
                        [
                            NotNode(ContainsNode(Role.dad)),
                            NotNode(ContainsNode(Role.mom)),
                        ]
                    )

                if new_roles:
                    roles_query.append(new_roles)
        StudyWrapper._add_roles_to_query(roles_query, kwargs)

        if rarity is not None:
            ultra_rare = rarity.get("ultraRare", None)
            ultra_rare = bool(ultra_rare)
            if ultra_rare and present_in_parent != {"neither"}:
                kwargs["ultra_rare"] = True
            else:
                max_alt_freq = rarity.get("maxFreq", None)
                min_alt_freq = rarity.get("minFreq", None)
                if min_alt_freq is not None or max_alt_freq is not None:
                    real_attr_filter = kwargs.get("real_attr_filter", [])
                    real_attr_filter.append(
                        ("af_allele_freq", (min_alt_freq, max_alt_freq))
                    )
                    kwargs["real_attr_filter"] = real_attr_filter
        kwargs.pop("presentInParent")

    def _transform_present_in_role(self, kwargs):
        roles_query = []

        for pir_id, filter_options in kwargs["presentInRole"].items():

            for filter_option in filter_options:
                new_roles = None

                if filter_option != "neither":
                    new_roles = ContainsNode(Role.from_name(filter_option))

                if filter_option == "neither":
                    new_roles = AndNode(
                        [
                            NotNode(ContainsNode(Role.from_name(role)))
                            for role in self.get_present_in_role(pir_id).roles
                        ]
                    )

                if new_roles:
                    roles_query.append(new_roles)

        kwargs.pop("presentInRole")

        self._add_roles_to_query(OrNode(roles_query), kwargs)

    def _transform_pedigree_filter_to_ids(self, pedigree_filter):
        column = pedigree_filter["source"]
        value = pedigree_filter["selection"]
        ped_df = self.families.ped_df.loc[
            self.families.ped_df[column] == value
        ]
        if pedigree_filter.get("role"):
            # Handle family filter
            ped_df = ped_df.loc[ped_df["role"] == pedigree_filter["role"]]
            ids = set(
                self.families.persons[person_id].family.family_id
                for person_id in ped_df["person_id"]
            )
        else:
            # Handle person filter
            ids = set(
                person_id for person_id in ped_df["person_id"]
                if person_id in self.families.persons
            )
        return ids

    def _transform_pheno_filter_to_ids(self, pheno_filter):
        pheno_filter = self.pheno_filter_builder.make_filter(pheno_filter)
        if pheno_filter.get("role"):
            # Handle family filter
            persons = set(
                p.person_id for p in self.families.persons_with_roles(
                    roles=[pheno_filter["role"]]
                )
            )
            measure_df = pheno_filter.apply(
                self.phenotype_data.get_measure_values_df(
                    pheno_filter["source"],
                    person_ids=persons,
                )
            )
            ids = set(
                self.families.persons[person_id].family.family_id
                for person_id in measure_df["person_id"]
            )
        else:
            # Handle person filter
            measure_df = pheno_filter.apply(
                self.phenotype_data.get_measure_values_df(
                    pheno_filter["source"]
                )
            )
            ids = set(
                person_id for person_id in measure_df["person_id"]
                if person_id in self.families.persons
            )
        return ids

    def _transform_filters_to_ids(self, filters: List[dict]) -> Set[str]:
        result = list()
        for filter_conf in filters:
            if filter_conf["from"] == "phenotype":
                ids = self._transform_pheno_filter_to_ids(filter_conf)
            else:
                ids = self._transform_pedigree_filter_to_ids(filter_conf)
            result.append(ids)
        return reduce(set.intersection, result)

    def _transform_person_filters(self, kwargs):
        matching_person_ids = self._transform_filters_to_ids(
            kwargs.pop("personFilters")
        )
        if matching_person_ids is not None:
            if "person_ids" in kwargs:
                matching_person_ids = set.intersection(
                    matching_person_ids, set(kwargs.pop("person_ids"))
                )
            kwargs["person_ids"] = matching_person_ids
        return kwargs

    def _transform_family_filters(self, kwargs):
        matching_family_ids = self._transform_filters_to_ids(
            kwargs.pop("familyFilters")
        )
        if matching_family_ids is not None:
            if "family_ids" in kwargs:
                matching_family_ids = set.intersection(
                    matching_family_ids, set(kwargs.pop("family_ids"))
                )
            kwargs["family_ids"] = matching_family_ids
        return kwargs

    @staticmethod
    def _add_roles_to_query(query, kwargs):
        if not query:
            return

        original_roles = kwargs.get("roles", None)
        if original_roles is not None:
            if isinstance(original_roles, str):
                original_roles = role_query.transform_query_string_to_tree(
                    original_roles
                )
            kwargs["roles"] = AndNode([original_roles, query])
        else:
            kwargs["roles"] = query

    @staticmethod
    def _add_inheritance_to_query(query, kwargs):
        if not query:
            return
        inheritance = kwargs.get("inheritance", [])
        if isinstance(inheritance, list):
            inheritance.append(query)
        elif isinstance(inheritance, str):
            inheritance = [inheritance]
            inheritance.append(query)
        else:
            raise ValueError(f"unexpected inheritance query {inheritance}")
        kwargs["inheritance"] = inheritance

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
            studyNames = []
            for studyId in result["studies"]:
                wrapper = gpf_instance.get_wdae_wrapper(studyId)
                name = (
                    wrapper.config.name
                    if wrapper.config.name is not None
                    else wrapper.config.id
                )
                studyNames.append(name)
                result["study_names"] = studyNames

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
        self.study_id = self.rest_client.get_remote_dataset_id(study_id)
        config = self.rest_client.get_dataset_config(self._remote_study_id)
        config["id"] = self.study_id
        config["name"] = f"({rest_client.remote_id}) {config['name']}"
        del config["access_rights"]
        del config["groups"]
        self.config = FrozenBox(config)

        self.phenotype_data = RemotePhenotypeData(
            self._remote_study_id,
            self.rest_client
        )

        self.is_remote = True

    def get_wdae_preview_info(self, query, max_variants_count=10000):
        query["datasetId"] = self._remote_study_id
        return self.rest_client.get_browser_preview_info(query)

    def get_variants_wdae_preview(self, query, max_variants_count=10000):

        study_filters = query.get("study_filters")
        if study_filters is not None:
            if self.study_id not in study_filters:
                return
            else:
                del query["study_filters"]

        query["datasetId"] = self._remote_study_id
        query["maxVariantsCount"] = max_variants_count
        response = self.rest_client.get_variants_preview(query)
        for line in response.iter_lines():
            if line:
                variants = json.loads(line)
                for variant in variants:
                    yield variant

    def get_variants_wdae_download(self, query, max_variants_count=10000):
        raise NotImplementedError

    def build_genotype_data_group_description(self, gpf_instance):
        return self.config.to_dict()
