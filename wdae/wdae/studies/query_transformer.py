import logging

from typing import List, Set

from functools import reduce

from dae.utils.effect_utils import EffectTypesMixin
from dae.variants.attributes import Role, Inheritance
from dae.utils.regions import Region
from dae.pedigrees.family import ALL_FAMILY_TYPES, FamilyType
from dae.backends.attributes_query import (
    role_query,
    variant_type_converter,
    sex_converter,
    AndNode,
    NotNode,
    OrNode,
    ContainsNode,
)

from dae.person_filters import make_pedigree_filter, make_pheno_filter

logger = logging.getLogger(__name__)


class QueryTransformer:

    FILTER_RENAMES_MAP = {
        "familyIds": "family_ids",
        "personIds": "person_ids",
        "gender": "sexes",
        "geneSymbols": "genes",
        "variantTypes": "variant_type",
        "effectTypes": "effect_types",
        "regionS": "regions",
    }

    def __init__(self, study_wrapper):
        self.study_wrapper = study_wrapper
        self.effect_types_mixin = EffectTypesMixin()

    def _transform_genomic_scores(self, genomic_scores):
        genomic_scores_filter = [
            (score["metric"], (score["rangeStart"], score["rangeEnd"]))
            for score in genomic_scores
            # if score["rangeStart"] or score["rangeEnd"]
        ]

        return genomic_scores_filter

    def _transform_gene_scores(self, gene_scores):
        if not self.study_wrapper.gene_scores_db:
            return

        scores_name = gene_scores.get("score", None)
        range_start = gene_scores.get("rangeStart", None)
        range_end = gene_scores.get("rangeEnd", None)

        if scores_name and scores_name in self.study_wrapper.gene_scores_db:
            score = self.study_wrapper.gene_scores_db[
                scores_name
            ]

            genes = score.get_genes(range_start, range_end)

            return list(genes)

    def _transform_min_max_alt_frequency(self, min_value, max_value):
        value_range = (min_value, max_value)

        if value_range == (None, None):
            return

        if value_range[0] is None:
            value_range = (float("-inf"), value_range[1])

        if value_range[1] is None:
            value_range = (value_range[0], float("inf"))

        value = "af_allele_freq"

        return (value, value_range)

    @staticmethod
    def _transform_present_in_child_and_parent_roles(
            present_in_child, present_in_parent):
        roles_query = []
        roles_query.append(
            QueryTransformer._present_in_child_to_roles(present_in_child))
        roles_query.append(
            QueryTransformer._present_in_parent_to_roles(present_in_parent))
        roles_query = list(filter(lambda rq: rq is not None, roles_query))
        if len(roles_query) == 2:
            roles_query = AndNode(roles_query)
        elif len(roles_query) == 1:
            roles_query = roles_query[0]
        else:
            roles_query = None

        return roles_query

    @staticmethod
    def _transform_present_in_child_and_parent_inheritance(
            present_in_child, present_in_parent,
            show_all_unknown=False):

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
                Inheritance.missing,
                Inheritance.omission
            ]
            if show_all_unknown:
                inheritance.append(Inheritance.unknown)

        inheritance = ",".join([str(inh) for inh in inheritance])
        return f"any({inheritance})"

    @staticmethod
    def _transform_present_in_child_and_parent_frequency(
            present_in_child, present_in_parent,
            rarity, frequency_filter):
        ultra_rare = rarity.get("ultraRare", None)
        ultra_rare = bool(ultra_rare)
        if ultra_rare:
            return ("ultra_rare", True)
        else:
            max_alt_freq = rarity.get("maxFreq", None)
            min_alt_freq = rarity.get("minFreq", None)
            if min_alt_freq is not None or max_alt_freq is not None:
                frequency_filter.append(
                    ("af_allele_freq", (min_alt_freq, max_alt_freq))
                )
                return ("frequency_filter", frequency_filter)
        return (None, None)

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

    def _transform_filters_to_ids(self, filters: List[dict]) -> Set[str]:
        result = list()
        for filter_conf in filters:
            roles = filter_conf.get("role") if "role" in filter_conf else None
            if filter_conf["from"] == "phenodb":
                ids = make_pheno_filter(
                    filter_conf, self.study_wrapper.phenotype_data
                ).apply(self.study_wrapper.families, roles)
            else:
                ids = make_pedigree_filter(filter_conf).apply(
                    self.study_wrapper.families, roles
                )
            result.append(ids)
        return reduce(set.intersection, result)

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

    def _add_roles_to_query(self, query, kwargs):
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

    def _handle_person_set_collection(self, kwargs):
        people_group = kwargs.pop("personSetCollection", {})
        logger.debug(f"person set collection requested: {people_group}")
        collection_id, selected_sets = None, None
        if people_group:
            collection_id = people_group["id"]
            selected_sets = people_group["checkedValues"]
        else:
            selected_person_set_collections = self.study_wrapper\
                .genotype_data\
                .config.person_set_collections\
                .selected_person_set_collections
            if selected_person_set_collections:
                collection_id = selected_person_set_collections[0]

        if collection_id is not None:
            kwargs["person_set_collection"] = collection_id, selected_sets
        return kwargs

    # Not implemented:
    # callSet
    # minParentsCalled
    # TMM_ALL
    def transform_kwargs(self, **kwargs):
        logger.debug(f"kwargs in study wrapper: {kwargs}")
        self._add_inheritance_to_query(
            "not possible_denovo and not possible_omission",
            kwargs
        )

        kwargs = self._handle_person_set_collection(kwargs)

        if "querySummary" in kwargs:
            kwargs["query_summary"] = kwargs["querySummary"]
            del kwargs["querySummary"]

        if "uniqueFamilyVariants" in kwargs:
            kwargs["unique_family_variants"] = kwargs["uniqueFamilyVariants"]
            del kwargs["uniqueFamilyVariants"]

        if "regions" in kwargs:
            kwargs["regions"] = list(map(Region.from_str, kwargs["regions"]))

        present_in_child = set()
        present_in_parent = set()
        rarity = None
        if "presentInChild" in kwargs or "presentInParent" in kwargs:
            if "presentInChild" in kwargs:
                present_in_child = set(kwargs["presentInChild"])
                kwargs.pop("presentInChild")

            if "presentInParent" in kwargs:
                present_in_parent = \
                    set(kwargs["presentInParent"]["presentInParent"])
                rarity = kwargs["presentInParent"].get("rarity", None)
                kwargs.pop("presentInParent")

            roles_query = self._transform_present_in_child_and_parent_roles(
                present_in_child, present_in_parent
            )
            self._add_roles_to_query(roles_query, kwargs)

            if present_in_parent != {"neither"} and rarity is not None:
                frequency_filter = kwargs.get("frequency_filter", [])
                arg, val = \
                    self._transform_present_in_child_and_parent_frequency(
                        present_in_child, present_in_parent,
                        rarity, frequency_filter
                    )
                if arg is not None:
                    kwargs[arg] = val

        show_all_unknown = \
            self.study_wrapper.config.genotype_browser.show_all_unknown

        if kwargs.get("inheritanceTypeFilter"):
            inheritance_types = set(kwargs["inheritanceTypeFilter"])
            if show_all_unknown \
                    and inheritance_types & {"mendelian", "missing"}:
                inheritance_types.add("unknown")

            query = "any({})".format(
                    ",".join(inheritance_types))

            self._add_inheritance_to_query(query, kwargs)
            kwargs.pop("inheritanceTypeFilter")
        else:
            inheritance = \
                self._transform_present_in_child_and_parent_inheritance(
                    present_in_child, present_in_parent, show_all_unknown)

            self._add_inheritance_to_query(inheritance, kwargs)

        if "genomicScores" in kwargs:
            genomic_scores = kwargs.pop("genomicScores", [])
            if "real_attr_filter" not in kwargs:
                kwargs["real_attr_filter"] = []
            kwargs["real_attr_filter"] += self._transform_genomic_scores(
                genomic_scores
            )

        if "geneScores" in kwargs:
            gene_scores = kwargs.pop("geneScores", {})
            genes = self._transform_gene_scores(gene_scores)
            if genes is not None:
                if "genes" not in kwargs:
                    kwargs["genes"] = []
                kwargs["genes"] += genes

        if "gender" in kwargs:
            sexes = set(kwargs["gender"])
            if sexes != set(["female", "male", "unspecified"]):
                sexes = [ContainsNode(sex_converter(sex)) for sex in sexes]
                kwargs["gender"] = OrNode(sexes)
            else:
                kwargs["gender"] = None

        if "variantTypes" in kwargs:
            variant_types = set(kwargs["variantTypes"])

            if variant_types != {"ins", "del", "sub", "CNV"}:
                if "CNV" in variant_types:
                    variant_types.remove("CNV")
                    variant_types.add("CNV+")
                    variant_types.add("CNV-")

                variant_types = [
                    ContainsNode(variant_type_converter(t))
                    for t in variant_types
                ]
                kwargs["variantTypes"] = OrNode(variant_types)
            else:
                del kwargs["variantTypes"]

        if "effectTypes" in kwargs:
            kwargs["effectTypes"] = self.effect_types_mixin.build_effect_types(
                kwargs["effectTypes"]
            )

        if kwargs.get("studyFilters"):
            request = set(kwargs["studyFilters"])
            if kwargs.get("allowed_studies") is not None:
                request = request & set(kwargs.pop("allowed_studies"))
            kwargs["study_filters"] = request

            del kwargs["studyFilters"]
        elif kwargs.get("allowed_studies") is not None:
            kwargs["study_filters"] = set(kwargs.pop("allowed_studies"))

        if "personFilters" in kwargs:
            person_filters = kwargs.pop("personFilters")
            if person_filters:
                matching_person_ids = self._transform_filters_to_ids(
                    person_filters
                )
                if matching_person_ids is not None and kwargs.get("personIds"):
                    kwargs["personIds"] = set.intersection(
                        matching_person_ids, set(kwargs.pop("personIds"))
                    )
                else:
                    kwargs["personIds"] = matching_person_ids

        if "familyFilters" in kwargs:
            family_filters = kwargs.pop("familyFilters")
            if family_filters:
                matching_family_ids = self._transform_filters_to_ids(
                    family_filters
                )
                if matching_family_ids is not None and kwargs.get("familyIds"):
                    kwargs["familyIds"] = set.intersection(
                        matching_family_ids, set(kwargs.pop("familyIds"))
                    )
                else:
                    kwargs["familyIds"] = matching_family_ids

        if "personIds" in kwargs:
            kwargs["personIds"] = list(kwargs["personIds"])

        if "familyTypes" in kwargs:
            family_ids_with_types = set()
            family_types = set([
                FamilyType.from_name(ft) for ft in kwargs["familyTypes"]])

            if family_types != ALL_FAMILY_TYPES:
                for family_type in family_types:
                    family_ids_with_types = set.union(
                        family_ids_with_types,
                        self.study_wrapper.families.families_by_type.get(
                            family_type, set()
                        )
                    )
                if "familyIds" in kwargs:
                    family_ids_with_types = set.intersection(
                        family_ids_with_types, set(kwargs.pop("familyIds"))
                    )
                kwargs["familyIds"] = family_ids_with_types

        if "affectedStatus" in kwargs:
            statuses = kwargs.pop("affectedStatus")
            kwargs["affected_status"] = [
                status.lower() for status in statuses
            ]

        for key in list(kwargs.keys()):
            if key in self.FILTER_RENAMES_MAP:
                kwargs[self.FILTER_RENAMES_MAP[key]] = kwargs[key]
                kwargs.pop(key)

        return kwargs
