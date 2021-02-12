import logging

from typing import List, Set

from functools import reduce

from dae.utils.effect_utils import (
    expand_effect_types,
)
from dae.variants.attributes import Role, Inheritance
from dae.utils.regions import Region
from dae.backends.attributes_query import (
    role_query,
    variant_type_converter,
    sex_converter,
    AndNode,
    NotNode,
    OrNode,
    ContainsNode,
)

logger = logging.getLogger(__name__)


class QueryTransformer:
    def __init__(self, study_wrapper):
        self.study_wrapper = study_wrapper

    def _transform_genomic_scores(self, genomic_scores):
        genomic_scores_filter = [
            (score["metric"], (score["rangeStart"], score["rangeEnd"]))
            for score in genomic_scores
            # if score["rangeStart"] or score["rangeEnd"]
        ]

        return genomic_scores_filter

    def _transform_gene_weights(self, gene_weights):
        if not self.study_wrapper.gene_weights_db:
            return

        weight_name = gene_weights.get("weight", None)
        range_start = gene_weights.get("rangeStart", None)
        range_end = gene_weights.get("rangeEnd", None)

        if weight_name and weight_name in self.gene_weights_db:
            weight = self.study_wrapper.gene_weights_db[
                gene_weights.get("weight")
            ]

            genes = weight.get_genes(range_start, range_end)

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

    def _transform_present_in_child_and_parent_roles(
            self, present_in_child, present_in_parent):
        roles_query = []
        roles_query.append(
            self._present_in_child_to_roles(present_in_child))
        roles_query.append(
            self._present_in_parent_to_roles(present_in_parent))
        roles_query = list(filter(lambda rq: rq is not None, roles_query))
        if len(roles_query) == 2:
            roles_query = AndNode(roles_query)
        elif len(roles_query) == 1:
            roles_query = roles_query[0]
        else:
            roles_query = None

        return roles_query

    def _transform_present_in_child_and_parent_inheritance(
            self, present_in_child, present_in_parent):
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
        return inheritance

    def _transform_present_in_child_and_parent_frequency(
            self, present_in_child, present_in_parent,
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

    def _transform_present_in_role(self, present_in_role):
        roles_query = []

        for pir_id, filter_options in present_in_role.items():

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

        return OrNode(roles_query)

    def _transform_pedigree_filter_to_ids(self, pedigree_filter):
        column = pedigree_filter["source"]
        value = set(pedigree_filter["selection"]["selection"])
        ped_df = self.study_wrapper.families.ped_df.loc[
            self.study_wrapper.families.ped_df[column].astype(str).isin(value)
        ]
        if pedigree_filter.get("role"):
            # Handle family filter
            ped_df = ped_df.loc[
                ped_df["role"].astype(str) == pedigree_filter["role"]
            ]
            ids = set(
                self.study_wrapper.families.persons[person_id].family.family_id
                for person_id in ped_df["person_id"]
            )
        else:
            # Handle person filter
            ids = set(
                person_id for person_id in ped_df["person_id"]
                if person_id in self.study_wrapper.families.persons
            )
        return ids

    def _transform_pheno_filter_to_ids(self, pheno_filter_conf):
        pheno_filter = self.study_wrapper.pheno_filter_builder.make_filter(
            pheno_filter_conf
        )
        if pheno_filter_conf.get("role"):
            # Handle family filter
            persons = set(
                p.person_id
                for p in self.study_wrapper.families.persons_with_roles(
                    roles=[pheno_filter_conf["role"]]
                )
            )
            measure_df = pheno_filter.apply(
                self.study_wrapper.phenotype_data.get_measure_values_df(
                    pheno_filter_conf["source"],
                    person_ids=persons,
                )
            )
            ids = set(
                self.study_wrapper.families.persons[person_id].family.family_id
                for person_id in measure_df["person_id"]
            )
        else:
            # Handle person filter
            measure_df = pheno_filter.apply(
                self.study_wrapper.phenotype_data.get_measure_values_df(
                    pheno_filter_conf["source"]
                )
            )
            ids = set(
                person_id for person_id in measure_df["person_id"]
                if person_id in self.study_wrapper.families.persons
            )
        return ids

    def _transform_filters_to_ids(self, filters: List[dict]) -> Set[str]:
        result = list()
        for filter_conf in filters:
            if filter_conf["from"] == "phenodb":
                ids = self._transform_pheno_filter_to_ids(filter_conf)
            else:
                ids = self._transform_pedigree_filter_to_ids(filter_conf)
            result.append(ids)
        return reduce(set.intersection, result)

    def _transform_person_filters(self, person_filters, person_ids=None):
        matching_person_ids = self._transform_filters_to_ids(
            person_filters
        )
        if matching_person_ids is not None:
            if person_ids is not None:
                matching_person_ids = set.intersection(
                    matching_person_ids, set(person_ids)
                )
        return matching_person_ids

    def _transform_family_filters(self, family_filters, family_ids=None):
        matching_family_ids = self._transform_filters_to_ids(
            family_filters
        )
        if matching_family_ids is not None:
            if family_ids is not None:
                matching_family_ids = set.intersection(
                    matching_family_ids, set(family_ids)
                )
        return matching_family_ids

    def _add_inheritance_to_query(self, query, kwargs):
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

    # Not implemented:
    # callSet
    # minParentsCalled
    # ultraRareOnly
    # TMM_ALL
    def transform_kwargs(self, **kwargs):
        logger.debug(f"kwargs in study wrapper: {kwargs}")
        self._add_inheritance_to_query(
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

            roles_query = self._transform_present_in_child_and_parent_roles(
                present_in_child, present_in_parent
            )
            self._add_roles_to_query(roles_query, kwargs)

            inheritance = \
                self._transform_present_in_child_and_parent_inheritance(
                    present_in_child, present_in_parent
                )
            self._add_inheritance_to_query(
                "any({})".format(",".join(inheritance)), kwargs)

            if present_in_parent != {"neither"} and rarity is not None:
                frequency_filter = kwargs.get("frequency_filter", [])
                arg, val = \
                    self._transform_present_in_child_and_parent_frequency(
                        present_in_child, present_in_parent,
                        rarity, frequency_filter
                    )
                if arg is not None:
                    kwargs[arg] = val

        if "presentInRole" in kwargs:
            present_in_role = kwargs.pop("presentInRole")
            roles_query = self._transform_present_in_role(present_in_role)
            self._add_roles_to_query(roles_query, kwargs)

        if (
            "minAltFrequencyPercent" in kwargs
            or "maxAltFrequencyPercent" in kwargs
        ):
            min_value = kwargs.pop("minAltFrequencyPercent", None)
            max_value = kwargs.pop("maxAltFrequencyPercent", None)
            if "real_attr_filter" not in kwargs:
                kwargs["real_attr_filter"] = []
            value_range = self._transform_min_max_alt_frequency(
                min_value, max_value
            )
            if value_range is not None:
                kwargs["real_attr_filter"].append(value_range)

        if "genomicScores" in kwargs:
            genomic_scores = kwargs.pop("genomicScores", [])
            if "real_attr_filter" not in kwargs:
                kwargs["real_attr_filter"] = []
            kwargs["real_attr_filter"] += self._transform_genomic_scores(
                genomic_scores
            )

        if "geneWeights" in kwargs:
            gene_weights = kwargs.pop("geneWeights", {})
            if "genes" not in kwargs:
                kwargs["genes"] = []
            kwargs["genes"] += self._transform_gene_weights(gene_weights)

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
            person_filters = kwargs.pop("personFilters")
            person_ids = kwargs.pop("person_ids", None)
            matching_person_ids = self._transform_person_filters(
                person_filters, person_ids
            )
            if matching_person_ids is not None:
                kwargs["person_ids"] = matching_person_ids

        if "familyFilters" in kwargs:
            family_filters = kwargs.pop("familyFilters")
            family_ids = kwargs.pop("family_ids", None)
            matching_family_ids = self._transform_family_filters(
                family_filters, family_ids
            )
            if matching_family_ids:
                kwargs["family_ids"] = matching_family_ids

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
