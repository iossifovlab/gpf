import logging
import time
from functools import reduce
from typing import Any, ClassVar, cast

from dae.effect_annotation.effect import EffectTypesMixin
from dae.person_filters import make_pedigree_filter, make_pheno_filter
from dae.person_filters.person_filters import make_pheno_filter_beta
from dae.person_sets import PSCQuery
from dae.query_variants.attributes_query import role_query
from dae.query_variants.sql.schema2.sql_query_builder import (
    SqlQueryBuilder,
    TagsQuery,
    ZygosityQuery,
)
from dae.utils.regions import Region
from dae.utils.variant_utils import BitmaskEnumTranslator
from dae.variants.attributes import Inheritance, Role, Zygosity

logger = logging.getLogger(__name__)


class QueryTransformer:
    """Transform genotype data query WEB parameters into query variants."""

    FILTER_RENAMES_MAP: ClassVar[dict[str, str]] = {
        "familyIds": "family_ids",
        "personIds": "person_ids",
        "genders": "sexes",
        "geneSymbols": "genes",
        "variantTypes": "variant_type",
        "effectTypes": "effect_types",
        "regionS": "regions",
    }

    def __init__(self, study_wrapper):  # type: ignore
        self.study_wrapper = study_wrapper
        self.effect_types_mixin = EffectTypesMixin()
        self.gpf_instance = study_wrapper.gpf_instance

    def _transform_genomic_scores_continuous(
        self, genomic_scores: list[dict],
    ) -> list[tuple[str, tuple[int | None, int | None]]]:
        return [
            (score["score"], (score["rangeStart"], score["rangeEnd"]))
            for score in genomic_scores
            if score["histogramType"] == "continuous"
        ]

    def _transform_genomic_scores_categorical(
        self, genomic_scores: list[dict],
    ) -> list[tuple[str, list[str | None]]]:
        return [
            (score["score"], score["values"])
            for score in genomic_scores
            if score["histogramType"] == "categorical"
        ]

    def _transform_gene_scores(self, gene_scores: dict) -> list[str] | None:
        if not self.study_wrapper.gene_scores_db:
            return None

        scores_name = gene_scores.get("score")
        range_start = gene_scores.get("rangeStart")
        range_end = gene_scores.get("rangeEnd")
        values = gene_scores.get("values")

        if scores_name and scores_name in self.study_wrapper.gene_scores_db:
            score_desc = self.study_wrapper.gene_scores_db[
                scores_name
            ]
            score = self.study_wrapper.gene_scores_db.get_gene_score(
                score_desc.resource_id,
            )

            genes = score.get_genes(scores_name, range_start, range_end, values)

            return list(genes)

        return None

    def _transform_min_max_alt_frequency(
        self, min_value: float | None, max_value: float | None,
    ) -> tuple[str, tuple[float, float]] | None:
        value_range = (min_value, max_value)

        if value_range == (None, None):
            return None

        result_range: tuple[float, float]
        if value_range[0] is None:
            assert value_range[1] is not None
            result_range = (float("-inf"), value_range[1])

        elif value_range[1] is None:
            assert value_range[0] is not None
            result_range = (value_range[0], float("inf"))
        else:
            assert value_range[0] is not None
            assert value_range[1] is not None
            result_range = cast(tuple[float, float], value_range)

        value = "af_allele_freq"

        return (value, result_range)

    @staticmethod
    def _transform_present_in_child_and_parent_roles(
        present_in_child: set[str],
        present_in_parent: set[str],
    ) -> str | None:
        roles_query = [
            QueryTransformer._present_in_child_to_roles(present_in_child),
            QueryTransformer._present_in_parent_to_roles(present_in_parent),
        ]
        result = [role for role in roles_query if role is not None]

        if len(result) == 2:
            return f"({result[0]}) and ({result[1]})"

        if len(result) == 1:
            return result[0]

        return None

    @staticmethod
    def _transform_present_in_child_and_parent_inheritance(
        present_in_child: set[str],
        present_in_parent: set[str],
    ) -> str:

        inheritance = None
        if present_in_child == {"neither"} and \
                present_in_parent != {"neither"}:
            inheritance = [
                Inheritance.mendelian, Inheritance.missing]
        elif present_in_child != {"neither"} and \
                present_in_parent == {"neither"}:
            inheritance = [Inheritance.denovo]
        else:
            inheritance = [
                Inheritance.denovo,
                Inheritance.mendelian,
                Inheritance.missing,
                Inheritance.omission,
                Inheritance.unknown,
            ]

        result = ",".join([str(inh) for inh in inheritance])
        return f"any({result})"

    @staticmethod
    def _transform_present_in_child_and_parent_frequency(
        _present_in_child: set[str], _present_in_parent: set[str],
        rarity: dict,
        frequency_filter: list[
            tuple[str, tuple[float | None, float | None]]],
    ) -> tuple[str | None, Any]:

        ultra_rare = rarity.get("ultraRare")
        ultra_rare = bool(ultra_rare)
        if ultra_rare:
            return ("ultra_rare", True)

        max_alt_freq = rarity.get("maxFreq")
        min_alt_freq = rarity.get("minFreq")
        if min_alt_freq is not None or max_alt_freq is not None:
            frequency_filter.append(
                ("af_allele_freq", (min_alt_freq, max_alt_freq)),
            )
            return ("frequency_filter", frequency_filter)

        return (None, None)

    @staticmethod
    def _present_in_child_to_roles(
        present_in_child: set[str],
    ) -> str | None:
        roles_query = []

        if "proband only" in present_in_child:
            roles_query.append("prb and not sib")

        if "sibling only" in present_in_child:
            roles_query.append("sib and not prb")

        if "proband and sibling" in present_in_child:
            roles_query.append("prb and sib")

        if "neither" in present_in_child:
            roles_query.append("not prb and not sib")
        if len(roles_query) == 4 or len(roles_query) == 0:
            return None
        if len(roles_query) == 1:
            return roles_query[0]
        return " or ".join(f"( {r} )" for r in roles_query)

    @staticmethod
    def _present_in_parent_to_roles(
        present_in_parent: set[str],
    ) -> str | None:
        roles_query = []

        if "mother only" in present_in_parent:
            roles_query.append("mom and not dad")

        if "father only" in present_in_parent:
            roles_query.append("dad and not mom")

        if "mother and father" in present_in_parent:
            roles_query.append("mom and dad")

        if "neither" in present_in_parent:
            roles_query.append("not mom and not dad")
        if len(roles_query) == 4 or len(roles_query) == 0:
            return None
        if len(roles_query) == 1:
            return roles_query[0]
        return " or ".join(f"( {r} )" for r in roles_query)

    def _transform_filters_to_ids(self, filters: list[dict]) -> set[str]:
        result = []
        for filter_conf in filters:
            roles = filter_conf.get("role") if "role" in filter_conf else None
            if filter_conf["from"] == "phenodb":
                ids = make_pheno_filter(
                    filter_conf, self.study_wrapper.phenotype_data,
                ).apply(self.study_wrapper.families, roles)
            else:
                ids = make_pedigree_filter(filter_conf).apply(
                    self.study_wrapper.families, roles,
                )
            result.append(ids)
        return reduce(set.intersection, result)

    def _transform_filters_to_ids_beta(self, filters: list[dict]) -> set[str]:
        result = []
        for filter_conf in filters:
            roles = filter_conf.get("roles") if "roles" in filter_conf else None
            ids = make_pheno_filter_beta(
                filter_conf, self.study_wrapper.phenotype_data,
            ).apply(self.study_wrapper.families, roles)

            result.append(ids)
        return reduce(set.intersection, result)

    @staticmethod
    def _add_inheritance_to_query(query: str, kwargs: dict[str, Any]) -> None:
        if not query:
            return
        inheritance = kwargs.get("inheritance", [])
        if isinstance(inheritance, list):
            inheritance.append(query)
        elif isinstance(inheritance, str):
            inheritance = [inheritance]
            inheritance.append(query)
        else:
            raise TypeError(f"unexpected inheritance query {inheritance}")
        kwargs["inheritance"] = inheritance

    @staticmethod
    def _add_roles_to_query(
        query: str | None, kwargs: dict[str, Any],
    ) -> str | None:
        if not query:
            return None

        original_roles = kwargs.get("roles")
        if original_roles is not None:
            if isinstance(original_roles, str):
                original_roles = role_query.transform_query_string_to_tree(
                    original_roles,
                )
            return f"{original_roles} and {query}"

        return query

    def _handle_person_set_collection(
        self, kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        psc_query = kwargs.pop("personSetCollection", {})
        logger.debug("person set collection requested: %s", psc_query)

        collection_id, selected_sets = None, None
        if psc_query:
            collection_id = psc_query["id"]
            selected_sets = psc_query["checkedValues"]
            kwargs["person_set_collection"] = PSCQuery(
                collection_id, set(selected_sets))
        else:
            # use default (first defined) person set collection
            # we need it for meaningful pedigree display
            person_set_collections = self.study_wrapper\
                .genotype_data.person_set_collections
            psc_id = next(iter(person_set_collections))
            default_psc = person_set_collections[psc_id]
            kwargs["person_set_collection"] = PSCQuery(
                psc_id, set(default_psc.person_sets.keys()),
            )

        return kwargs

    def _transform_regions(self, regions: list[str]) -> list[Region]:
        result = list(map(Region.from_str, regions))
        chrom_prefix = self.gpf_instance.reference_genome.chrom_prefix
        chromosomes = set(self.gpf_instance.reference_genome.chromosomes)
        for region in result:
            if region.chrom not in chromosomes:
                if chrom_prefix == "chr":
                    region.chrom = f"{chrom_prefix}{region.chrom}"
                    if chrom_prefix not in chromosomes:
                        continue
                elif chrom_prefix == "":
                    region.chrom = region.chrom.lstrip("chr")
                    if region.chrom not in chromosomes:
                        continue
                else:
                    continue
        return result

    def transform_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Transform WEB query variants params into genotype data params."""
        # flake8: noqa: C901
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        start = time.time()
        logger.debug("kwargs in study wrapper: %s", kwargs)
        self._add_inheritance_to_query(
            "not possible_denovo and not possible_omission",
            kwargs,
        )

        kwargs = self._handle_person_set_collection(kwargs)

        kwargs["tags_query"] = TagsQuery(
            selected_family_tags=kwargs.get("selectedFamilyTags"),
            deselected_family_tags=kwargs.get("deselectedFamilyTags"),
            tags_or_mode=not bool(kwargs.get("tagIntersection", "True")),
    )

        if "querySummary" in kwargs:
            kwargs["query_summary"] = kwargs["querySummary"]
            del kwargs["querySummary"]

        if "uniqueFamilyVariants" in kwargs:
            kwargs["unique_family_variants"] = kwargs["uniqueFamilyVariants"]
            del kwargs["uniqueFamilyVariants"]

        if "regions" in kwargs:
            kwargs["regions"] = self._transform_regions(kwargs["regions"])

        present_in_child = set()
        present_in_parent = set()
        rarity = None
        if "presentInChild" in kwargs or "presentInParent" in kwargs:
            if "presentInChild" in kwargs:
                present_in_child = set(kwargs["presentInChild"])
                kwargs.pop("presentInChild")
                children_roles_query = \
                    self._present_in_child_to_roles(present_in_child)
                children_roles_query = \
                    self._add_roles_to_query(children_roles_query, kwargs)
                kwargs["roles_in_child"] = children_roles_query

            if "presentInParent" in kwargs:
                present_in_parent = \
                    set(kwargs["presentInParent"]["presentInParent"])
                rarity = kwargs["presentInParent"].get("rarity", None)
                kwargs.pop("presentInParent")
                parent_roles_query = \
                    self._present_in_parent_to_roles(present_in_parent)

                parent_roles_query = \
                    self._add_roles_to_query(parent_roles_query, kwargs)

                kwargs["roles_in_parent"] = parent_roles_query

            if present_in_parent != {"neither"} and rarity is not None:
                frequency_filter = kwargs.get("frequency_filter", [])
                arg, val = \
                    self._transform_present_in_child_and_parent_frequency(
                        present_in_child, present_in_parent,
                        rarity, frequency_filter,
                    )
                if arg is not None:
                    kwargs[arg] = val

        if kwargs.get("inheritanceTypeFilter"):
            inheritance_types = set(kwargs["inheritanceTypeFilter"])
            if inheritance_types & {"mendelian", "missing"}:
                inheritance_types.add("unknown")

            query = f"any({','.join(inheritance_types)})"

            self._add_inheritance_to_query(query, kwargs)
            kwargs.pop("inheritanceTypeFilter")
        else:
            inheritance = \
                self._transform_present_in_child_and_parent_inheritance(
                    present_in_child, present_in_parent)

            self._add_inheritance_to_query(inheritance, kwargs)

        if "genomicScores" in kwargs:
            genomic_scores = kwargs.pop("genomicScores", [])
            if "real_attr_filter" not in kwargs:
                kwargs["real_attr_filter"] = []
            kwargs["real_attr_filter"].extend(
                self._transform_genomic_scores_continuous(genomic_scores))
            if "categorical_attr_filter" not in kwargs:
                kwargs["categorical_attr_filter"] = []
            kwargs["categorical_attr_filter"].extend(
                self._transform_genomic_scores_categorical(genomic_scores))

        if "frequencyScores" in kwargs:
            frequency_scores = kwargs.pop("frequencyScores", [])
            if "frequency_filter" not in kwargs:
                kwargs["frequency_filter"] = []
            kwargs["frequency_filter"].extend(
                self._transform_genomic_scores_continuous(frequency_scores))

        if "geneScores" in kwargs:
            gene_scores = kwargs.pop("geneScores", {})
            genes = self._transform_gene_scores(gene_scores)
            if genes is not None:
                if "genes" not in kwargs:
                    kwargs["genes"] = []
                kwargs["genes"] += genes

        if "genders" in kwargs:
            sexes = set(kwargs["genders"])
            if sexes != {"female", "male", "unspecified"}:
                sexes_query = f"any({','.join(sexes)})"
                kwargs["genders"] = sexes_query
            else:
                kwargs["genders"] = None

        if "variantTypes" in kwargs:
            variant_types = set(kwargs["variantTypes"])

            if variant_types != {"ins", "del", "sub", "CNV", "complex"}:
                if "CNV" in variant_types:
                    variant_types.remove("CNV")
                    variant_types.add("CNV+")
                    variant_types.add("CNV-")
                variant_types_query = f"any({','.join(variant_types)})"
                kwargs["variantTypes"] = variant_types_query
            else:
                del kwargs["variantTypes"]

        if "effectTypes" in kwargs:
            kwargs["effectTypes"] = self.effect_types_mixin.build_effect_types(
                kwargs["effectTypes"],
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
                    person_filters,
                )
                if matching_person_ids is not None and kwargs.get("personIds"):
                    kwargs["personIds"] = set.intersection(
                        matching_person_ids, set(kwargs.pop("personIds")),
                    )
                else:
                    kwargs["personIds"] = matching_person_ids

        if "personFiltersBeta" in kwargs:
            person_filters = kwargs.pop("personFiltersBeta")
            if person_filters:
                matching_person_ids = self._transform_filters_to_ids_beta(
                    person_filters,
                )
                if matching_person_ids is not None and kwargs.get("personIds"):
                    kwargs["personIds"] = set.intersection(
                        matching_person_ids, set(kwargs.pop("personIds")),
                    )
                else:
                    kwargs["personIds"] = matching_person_ids

        if "familyFilters" in kwargs:
            family_filters = kwargs.pop("familyFilters")
            if family_filters:
                matching_family_ids = self._transform_filters_to_ids(
                    family_filters,
                )
                if matching_family_ids is not None and kwargs.get("familyIds"):
                    kwargs["familyIds"] = set.intersection(
                        matching_family_ids, set(kwargs.pop("familyIds")),
                    )
                else:
                    kwargs["familyIds"] = matching_family_ids

        if "familyFiltersBeta" in kwargs:
            family_filters = kwargs.pop("familyFiltersBeta")
            if family_filters:
                matching_family_ids = self._transform_filters_to_ids_beta(
                    family_filters,
                )
                if matching_family_ids is not None and kwargs.get("familyIds"):
                    kwargs["familyIds"] = set.intersection(
                        matching_family_ids, set(kwargs.pop("familyIds")),
                    )
                else:
                    kwargs["familyIds"] = matching_family_ids

        kwargs["zygosity_query"] = ZygosityQuery()
        if "zygosityInStatus" in kwargs:
            zygosity = kwargs.pop("zygosityInStatus")
            if not isinstance(zygosity, str):
                raise ValueError(
                    "Invalid zygosity in status argument - not a string.",
                )

            zygosity = zygosity.lower()

            if zygosity not in ["homozygous", "heterozygous"]:
                raise ValueError(
                    f"Invalid zygosity in status value {zygosity},"
                    "expected either homozygous or heterozygous.",
                )

            kwargs["zygosity_query"].status_zygosity = zygosity

        translator = BitmaskEnumTranslator(
            main_enum_type=Zygosity, partition_by_enum_type=Role,
        )
        if "zygosityInParent" in kwargs:
            zygosity = kwargs.pop("zygosityInParent")
            if not isinstance(zygosity, str):
                raise ValueError(
                    "Invalid zygosity in parents argument - not a string.",
                )
            if "roles_in_parent" not in kwargs:
                raise ValueError(
                    "Missing present in parent for parent zygosity",
                )

            roles_in_parent = kwargs["roles_in_parent"]

            zygosity = zygosity.lower()

            if zygosity not in ["homozygous", "heterozygous"]:
                raise ValueError(
                    f"Invalid zygosity in parents value {zygosity},"
                    "expected either homozygous or heterozygous.",
                )
            mask = 0
            if roles_in_parent is None:
                mask = translator.apply_mask(
                    mask, Zygosity.from_name(zygosity).value, Role.mom,
                )
                mask = translator.apply_mask(
                    mask, Zygosity.from_name(zygosity).value, Role.dad,
                )
            else:
                if SqlQueryBuilder.check_roles_query_value(
                    cast(str, roles_in_parent), Role.mom.value,
                ):
                    mask = translator.apply_mask(
                        mask, Zygosity.from_name(zygosity).value, Role.mom,
                    )
                if SqlQueryBuilder.check_roles_query_value(
                    cast(str, roles_in_parent), Role.dad.value,
                ):
                    mask = translator.apply_mask(
                        mask, Zygosity.from_name(zygosity).value, Role.dad,
                    )
                if SqlQueryBuilder.check_roles_query_value(
                    cast(str, roles_in_parent), Role.mom.value | Role.dad.value,
                ):
                    mask = translator.apply_mask(
                        mask, Zygosity.from_name(zygosity).value, Role.dad,
                    )
                    mask = translator.apply_mask(
                        mask, Zygosity.from_name(zygosity).value, Role.mom,
                    )
            kwargs["zygosity_query"].parents_zygosity = mask

        if "zygosityInChild" in kwargs:
            zygosity = kwargs.pop("zygosityInChild")
            if not isinstance(zygosity, str):
                raise ValueError(
                    "Invalid zygosity in children argument - not a string.",
                )

            if "roles_in_child" not in kwargs:
                raise ValueError(
                    "Missing present in child for child zygosity",
                )

            roles_in_child = kwargs["roles_in_child"]

            zygosity = zygosity.lower()

            if zygosity not in ["homozygous", "heterozygous"]:
                raise ValueError(
                    f"Invalid zygosity in children value {zygosity},"
                    "expected either homozygous or heterozygous.",
                )

            mask = 0

            if roles_in_child is None:
                mask = translator.apply_mask(
                    mask, Zygosity.from_name(zygosity).value, Role.prb,
                )
                mask = translator.apply_mask(
                    mask, Zygosity.from_name(zygosity).value, Role.sib,
                )

            else:
                if SqlQueryBuilder.check_roles_query_value(
                    cast(str, roles_in_child), Role.prb.value,
                ):
                    mask = translator.apply_mask(
                        mask, Zygosity.from_name(zygosity).value, Role.prb,
                    )
                if SqlQueryBuilder.check_roles_query_value(
                    cast(str, roles_in_child), Role.sib.value,
                ):
                    mask = translator.apply_mask(
                        mask, Zygosity.from_name(zygosity).value, Role.sib,
                    )
                if SqlQueryBuilder.check_roles_query_value(
                    cast(str, roles_in_child), Role.prb.value | Role.sib.value,
                ):
                    mask = translator.apply_mask(
                        mask, Zygosity.from_name(zygosity).value, Role.prb,
                    )
                    mask = translator.apply_mask(
                        mask, Zygosity.from_name(zygosity).value, Role.sib,
                    )
            kwargs["zygosity_query"].children_zygosity = mask

        if "personIds" in kwargs:
            kwargs["personIds"] = list(kwargs["personIds"])

        if "affectedStatus" in kwargs:
            statuses = kwargs.pop("affectedStatus")
            kwargs["affected_status"] = [
                status.lower() for status in statuses
            ]

        for key in list(kwargs.keys()):
            if key in self.FILTER_RENAMES_MAP:
                kwargs[self.FILTER_RENAMES_MAP[key]] = kwargs[key]
                kwargs.pop(key)

        elapsed = time.time() - start
        logger.debug("transform kwargs took %.2f sec", elapsed)

        return kwargs
