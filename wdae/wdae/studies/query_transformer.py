from __future__ import annotations

import logging
import time
from functools import reduce
from threading import Lock
from typing import Any, ClassVar, cast

from dae.effect_annotation.effect import EffectTypesMixin
from dae.gene_scores.gene_scores import GeneScoresDb
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.person_filters import make_pedigree_filter, make_pheno_filter
from dae.person_filters.person_filters import make_pheno_filter_beta
from dae.person_sets import PSCQuery
from dae.person_sets.person_sets import (
    AttributeQueriesUnsupportedException,
)
from dae.query_variants.attribute_queries import (
    update_attribute_query_with_compounds,
)
from dae.query_variants.sql.schema2.sql_query_builder import (
    TagsQuery,
)
from dae.studies.study import GenotypeDataStudy
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance, Zygosity
from dae.variants.core import Allele

from studies.study_wrapper import (
    QueryTransformerProtocol,
    WDAEAbstractStudy,
)

logger = logging.getLogger(__name__)

_QUERY_TRANSFORMER: QueryTransformer | None = None
_QUERY_TRANSFORMER_LOCK = Lock()


class QueryTransformer(QueryTransformerProtocol):
    """Transform genotype data query WEB parameters into query variants."""

    FILTER_RENAMES_MAP: ClassVar[dict[str, str]] = {
        "familyIds": "family_ids",
        "personIds": "person_ids",
        "genders": "sexes",
        "geneSymbols": "genes",
        "variantTypes": "variant_type",
        "effectTypes": "effect_types",
        "regionS": "regions",
        "maxVariantsCount": "limit",
    }

    def __init__(
        self, gene_scores_db: GeneScoresDb,
        chromosomes: list[str], chr_prefix: str,
    ) -> None:
        self.gene_scores_db = gene_scores_db
        self.chromosomes = chromosomes
        self.chr_prefix = chr_prefix
        self.effect_types_mixin = EffectTypesMixin()

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
        if not self.gene_scores_db:
            return None

        scores_name = gene_scores.get("score")
        range_start = gene_scores.get("rangeStart")
        range_end = gene_scores.get("rangeEnd")
        values = gene_scores.get("values")

        if scores_name and scores_name in self.gene_scores_db:
            score_desc = self.gene_scores_db[
                scores_name
            ]
            score = self.gene_scores_db.get_gene_score(
                score_desc.resource_id,
            )
            if score is None:
                return None

            genes = score.get_genes(
                scores_name, range_start, range_end, values)

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
        kwargs: dict[str, Any],
    ) -> str | None:
        present_in_child = None
        present_in_parent = None
        if "presentInChild" in kwargs:
            present_in_child = kwargs.pop("presentInChild")
        if "presentInParent" in kwargs:
            present_in_parent = kwargs.pop("presentInParent")

        roles_query = [present_in_child, present_in_parent]
        result = [role for role in roles_query if role is not None]

        if len(result) == 2:
            return f"({result[0]}) and ({result[1]})"

        if len(result) == 1:
            return cast(str, result[0])

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
        return f"any([{result}])"

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
        zygosity: str | None = None,
    ) -> str | None:
        roles_query = []

        if "proband only" in present_in_child:
            roles_query.append("prb and not sib")

        if "sibling only" in present_in_child:
            roles_query.append("sib and not prb")

        if "proband and sibling" in present_in_child:
            roles_query.append("prb and sib")

        if len(roles_query) > 0 and zygosity is not None:
            current_query = " or ".join(f"({r})" for r in roles_query)
            roles_query = [
                update_attribute_query_with_compounds(
                    current_query, zygosity,
                ).lstrip("(").rstrip(")"),
            ]

        if "neither" in present_in_child:
            roles_query.append("not prb and not sib")
        if (len(roles_query) == 4) or len(roles_query) == 0:
            return None
        if len(roles_query) == 1:
            return roles_query[0]
        return " or ".join(f"({r})" for r in roles_query)

    @staticmethod
    def _present_in_parent_to_roles(
        present_in_parent: set[str],
        zygosity: str | None = None,
    ) -> str | None:
        roles_query = []

        if "mother only" in present_in_parent:
            roles_query.append("mom and not dad")

        if "father only" in present_in_parent:
            roles_query.append("dad and not mom")

        if "mother and father" in present_in_parent:
            roles_query.append("mom and dad")

        if len(roles_query) > 0 and zygosity is not None:
            current_query = " or ".join(f"({r})" for r in roles_query)
            roles_query = [
                update_attribute_query_with_compounds(
                    current_query, zygosity,
                ).lstrip("(").rstrip(")"),
            ]

        if "neither" in present_in_parent:
            roles_query.append("not mom and not dad")
        if (len(roles_query) == 4) or len(roles_query) == 0:
            return None
        if len(roles_query) == 1:
            return roles_query[0]
        return " or ".join(f"({r})" for r in roles_query)

    def _transform_filters_to_ids(
        self, filters: list[dict],
        study_wrapper: WDAEAbstractStudy,
    ) -> set[str]:
        result = []
        for filter_conf in filters:
            roles = filter_conf.get("role") if "role" in filter_conf else None
            if filter_conf["from"] == "phenodb":
                ids = make_pheno_filter(
                    filter_conf, study_wrapper.phenotype_data,
                ).apply(study_wrapper.families, roles)
            else:
                ids = make_pedigree_filter(filter_conf).apply(
                    study_wrapper.families, roles,
                )
            result.append(ids)
        return reduce(set.intersection, result)

    def _transform_pheno_filters_to_ids(
        self, filters: list[dict],
        study_wrapper: WDAEAbstractStudy,
    ) -> set[str]:
        result = []
        for filter_conf in filters:
            roles = filter_conf.get("roles") if "roles" in filter_conf else None
            ids = make_pheno_filter_beta(
                filter_conf, study_wrapper.phenotype_data,
            ).apply(study_wrapper.families, roles)

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

    def extract_person_set_collection_query(
            self, study: WDAEAbstractStudy, kwargs: dict[str, Any],
    ) -> PSCQuery:
        psc_query_raw = kwargs.pop("personSetCollection", {})
        logger.debug("person set collection requested: %s", psc_query_raw)

        if psc_query_raw:
            collection_id = psc_query_raw["id"]
            selected_sets = psc_query_raw["checkedValues"]
            psc_query = PSCQuery(collection_id, set(selected_sets))
        else:
            # use default (first defined) person set collection
            # we need it for meaningful pedigree display
            person_set_collections = study\
                .genotype_data.person_set_collections
            psc_id = next(iter(person_set_collections))
            default_psc = person_set_collections[psc_id]
            psc_query = PSCQuery(
                psc_id, set(default_psc.person_sets.keys()),
            )
        return psc_query

    def _handle_person_set_collection(
        self, study_wrapper: WDAEAbstractStudy, kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        psc_query = \
            self.extract_person_set_collection_query(study_wrapper, kwargs)
        kwargs["person_set_collection"] = psc_query

        if not study_wrapper.is_genotype:
            raise ValueError(
                "Cannot handle person set collection "
                "query argument on non genotype studies.",
            )
        psc = study_wrapper.get_person_set_collection(
            psc_query.psc_id,
        )
        assert psc is not None

        if study_wrapper.is_group:
            return {}
        genotype_data = cast(GenotypeDataStudy, study_wrapper.genotype_data)

        # Handling of person set collections for roles and sexes
        # is not implemented here for backends which do not
        # support affected status intentionally.
        # This is left as a problem for later as the design decisions
        # behind how this should get handled were getting way too
        # complicated for a feature that has barely seen use.
        if genotype_data.backend.has_affected_status_queries():
            try:
                psc_queries = psc.transform_ps_query_to_attribute_queries(
                    psc_query,
                )
            except AttributeQueriesUnsupportedException:
                person_ids = kwargs.get("personIds")
                psc_person_ids = psc.query_person_ids(psc_query)
                if psc_person_ids is not None:
                    if person_ids is None:
                        person_ids = psc_person_ids
                    else:
                        person_ids = person_ids.intersection(
                            psc_person_ids,
                        )
                if person_ids is not None:
                    kwargs["personIds"] = person_ids
            else:
                kwargs.update(psc_queries)

        return kwargs

    def _transform_regions(self, regions: list[str]) -> list[Region]:
        result = list(map(Region.from_str, regions))
        chrom_prefix = self.chr_prefix
        chromosomes = self.chromosomes
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

    def _apply_zygosity(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        valid_zygosities = [v.name for v in Zygosity]
        if "genders" in kwargs and "zygosityInSexes" in kwargs:
            zygosity = kwargs.pop("zygosityInSexes")
            if not isinstance(zygosity, str):
                raise ValueError(
                    "Invalid zygosity in sexes argument - not a string.",
                )
            if zygosity not in valid_zygosities:
                raise ValueError(
                    f"Invalid zygosity in sexes {zygosity}, "
                    f"expected one of {valid_zygosities}",
                )
            kwargs["genders"] = update_attribute_query_with_compounds(
                kwargs["genders"], zygosity,
            )

        if "status" in kwargs and "zygosityInStatus" in kwargs:
            zygosity = kwargs.pop("zygosityInStatus")
            if not isinstance(zygosity, str):
                raise ValueError(
                    "Invalid zygosity in status argument - not a string.",
                )

            zygosity = zygosity.lower()

            if zygosity not in valid_zygosities:
                raise ValueError(
                    f"Invalid zygosity in status {zygosity}, "
                    f"expected one of {valid_zygosities}",
                )
            kwargs["status"] = update_attribute_query_with_compounds(
                kwargs["status"], zygosity,
            )

        return kwargs

    def get_unique_family_variants(self, kwargs: dict[str, Any]) -> bool:
        if "uniqueFamilyVariants" not in kwargs:
            return False
        return bool(kwargs["uniqueFamilyVariants"])

    def transform_kwargs(
        self, study: WDAEAbstractStudy, **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Transform WEB query variants params into genotype data params.

        Requires a study wrapper to handle study context specific arguments,
        such as person set collections and phenotype filters.

        Returns None if the query is deemed empty.
        """
        # flake8: noqa: C901
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        start = time.time()
        logger.debug("kwargs in study wrapper %s: %s", study.study_id, kwargs)

        if kwargs.get("personIds"):
            # Temporarily transform to set for easier combining of person IDs.
            kwargs["personIds"] = set(kwargs["personIds"])

        self._add_inheritance_to_query(
            "not possible_denovo and not possible_omission",
            kwargs,
        )

        if kwargs.get("personSetCollection"):
            kwargs = self._handle_person_set_collection(study, kwargs)

        kwargs["tags_query"] = TagsQuery(
            selected_family_tags=kwargs.get("selectedFamilyTags"),
            deselected_family_tags=kwargs.get("deselectedFamilyTags"),
            tags_or_mode=not bool(kwargs.get("tagIntersection", "True")),
        )

        if "querySummary" in kwargs:
            kwargs["query_summary"] = kwargs["querySummary"]
            del kwargs["querySummary"]

        if "uniqueFamilyVariants" in kwargs:
            kwargs["unique_family_variants"] = self.get_unique_family_variants(
                kwargs)
            del kwargs["uniqueFamilyVariants"]

        if "regions" in kwargs:
            kwargs["regions"] = self._transform_regions(kwargs["regions"])

        present_in_child = set()
        present_in_parent = set()
        rarity = None
        if "presentInChild" in kwargs:
            present_in_child = set(kwargs["presentInChild"])
            zygosity = kwargs.pop("zygosityInChild", None)

            kwargs["presentInChild"] = self._present_in_child_to_roles(
                present_in_child,
                zygosity,
            )

        if "presentInParent" in kwargs:
            present_in_parent = \
                set(kwargs["presentInParent"]["presentInParent"])
            zygosity = kwargs.pop("zygosityInParent", None)
            rarity = kwargs["presentInParent"].get("rarity", None)
            kwargs["presentInParent"] = self._present_in_parent_to_roles(
                present_in_parent,
                zygosity,
            )

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

            query = f"any([{','.join(inheritance_types)}])"

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
                sexes = {f"{sex}" for sex in sexes}
                sexes_query = f"any([{','.join(sexes)}])"
                kwargs["genders"] = sexes_query
            else:
                kwargs["genders"] = None

        if "variantTypes" in kwargs:
            variant_types = {
                Allele.DISPLAY_NAME_TYPE[vt.lower()]
                for vt in kwargs["variantTypes"]
            }

            if variant_types != {
                "small_insertion",
                "small_deletion",
                "substitution",
                "cnv",
                "complex",
            }:
                if "cnv" in variant_types:
                    variant_types.remove("cnv")
                    variant_types.add("cnv+")
                    variant_types.add("cnv-")
                variant_types_query = f"{' or '.join(variant_types)}"
                kwargs["variantTypes"] = variant_types_query
            else:
                del kwargs["variantTypes"]

        if "effectTypes" in kwargs:
            kwargs["effectTypes"] = self.effect_types_mixin.build_effect_types(
                kwargs["effectTypes"],
            )

        if kwargs.get("personFilters"):
            person_filters = kwargs.pop("personFilters")
            if person_filters:
                matching_person_ids = self._transform_filters_to_ids(
                    person_filters,
                    study,
                )
                if matching_person_ids is not None and kwargs.get("personIds"):
                    kwargs["personIds"] = set.intersection(
                        matching_person_ids, set(kwargs.pop("personIds")),
                    )
                else:
                    kwargs["personIds"] = matching_person_ids

        if kwargs.get("personFiltersBeta"):
            person_filters = kwargs.pop("personFiltersBeta")
            if person_filters:
                matching_person_ids = self._transform_pheno_filters_to_ids(
                    person_filters,
                    study,
                )
                if matching_person_ids is not None and kwargs.get("personIds"):
                    kwargs["personIds"] = set.intersection(
                        matching_person_ids, set(kwargs.pop("personIds")),
                    )
                else:
                    kwargs["personIds"] = matching_person_ids

        if kwargs.get("familyFilters"):
            family_filters = kwargs.pop("familyFilters")
            if family_filters:
                matching_family_ids = self._transform_filters_to_ids(
                    family_filters,
                    study,
                )
                if matching_family_ids is not None and kwargs.get("familyIds"):
                    kwargs["familyIds"] = set.intersection(
                        matching_family_ids, set(kwargs.pop("familyIds")),
                    )
                else:
                    kwargs["familyIds"] = matching_family_ids

        if kwargs.get("familyPhenoFilters"):
            family_filters = kwargs.pop("familyPhenoFilters")
            if family_filters:
                matching_family_ids = self._transform_pheno_filters_to_ids(
                    family_filters,
                    study,
                )
                if matching_family_ids is not None and kwargs.get("familyIds"):
                    kwargs["familyIds"] = set.intersection(
                        matching_family_ids, set(kwargs.pop("familyIds")),
                    )
                else:
                    kwargs["familyIds"] = matching_family_ids

        if kwargs.get("personIds"):
            kwargs["personIds"] = list(kwargs["personIds"])

        if "affectedStatus" in kwargs:
            statuses = kwargs.pop("affectedStatus")
            kwargs["affected_status"] = [
                status.lower() for status in statuses
            ]

        if "summaryVariantIds" in kwargs:
            summary_variant_ids = kwargs.pop("summaryVariantIds")
            kwargs["summary_variant_ids"] = summary_variant_ids

        self._apply_zygosity(kwargs)

        kwargs["roles"] = self._transform_present_in_child_and_parent_roles(
            kwargs,
        )

        study_filters = None
        if kwargs.get("allowed_studies") is not None:
            study_filters = set(kwargs.pop("allowed_studies"))

        if kwargs.get("studyFilters"):
            if study_filters is not None:
                study_filters = study_filters & set(kwargs.pop("studyFilters"))
            else:
                study_filters = set(kwargs.pop("studyFilters"))

        kwargs["study_filters"] = study_filters

        for key in list(kwargs.keys()):
            if key in self.FILTER_RENAMES_MAP:
                kwargs[self.FILTER_RENAMES_MAP[key]] = kwargs[key]
                kwargs.pop(key)

        elapsed = time.time() - start
        logger.debug("transform kwargs took %.2f sec", elapsed)

        return kwargs


def make_query_transformer(gpf_instance: GPFInstance) -> QueryTransformer:
    return QueryTransformer(
        gpf_instance.gene_scores_db,
        gpf_instance.reference_genome.chromosomes,
        gpf_instance.reference_genome.chrom_prefix,
    )


def get_or_create_query_transformer(
    gpf_instance: GPFInstance,
) -> QueryTransformer:
    """Get or create query transformer singleton instance."""
    global _QUERY_TRANSFORMER  # pylint: disable=global-statement

    with _QUERY_TRANSFORMER_LOCK:
        if _QUERY_TRANSFORMER is not None:
            return _QUERY_TRANSFORMER

        _QUERY_TRANSFORMER = QueryTransformer(
            gpf_instance.gene_scores_db,
            gpf_instance.reference_genome.chromosomes,
            gpf_instance.reference_genome.chrom_prefix,
        )
        return _QUERY_TRANSFORMER
