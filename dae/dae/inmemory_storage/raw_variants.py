import abc
import logging
import queue
from collections.abc import Callable, Iterator, Sequence
from contextlib import closing
from functools import reduce
from typing import Any, cast

from dae.pedigrees.families_data import FamiliesData
from dae.query_variants.attributes_query import (
    Matcher,
    affected_status_query,
    inheritance_query,
    role_query,
    sex_query,
    variant_type_query,
)
from dae.query_variants.base_query_variants import (
    QueryVariantsBase,
)
from dae.query_variants.query_runners import QueryResult, QueryRunner
from dae.query_variants.sql.schema2.sql_query_builder import TagsQuery
from dae.utils.regions import Region
from dae.variants.attributes import Inheritance
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.variant import SummaryAllele, SummaryVariant

RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]
logger = logging.getLogger(__name__)


class RawVariantsQueryRunner(QueryRunner):
    """Run a variant iterator as a query."""

    def __init__(
        self, variants_iterator: Iterator[Any],
        deserializer: Callable | None = None,
    ) -> None:
        super().__init__(deserializer=deserializer)
        self.variants_iterator = variants_iterator
        assert self.variants_iterator is not None

    def run(self) -> None:
        assert self._result_queue is not None
        try:
            if self.is_closed():
                return

            while True:
                row = next(self.variants_iterator)
                if row is None:
                    break
                val = self.deserializer(row)
                if val is None:
                    continue

                while True:
                    try:
                        self.put_value_in_result_queue(val)
                        break
                    except queue.Full:
                        if self.is_closed():
                            break

                if self.is_closed():
                    break

        except StopIteration:
            logger.debug("variants iterator done")

        except BaseException as ex:  # pylint: disable=broad-except
            logger.exception("exception in runner run")
            self.put_value_in_result_queue(ex)

        finally:
            self.close()

        with self._status_lock:
            self._done = True
        logger.debug("raw variants query runner done")


class RawFamilyVariants(abc.ABC):
    """Base class that stores a reference to the families data."""

    def __init__(self, families: FamiliesData) -> None:
        self.families = families

    @abc.abstractmethod
    def full_variants_iterator(
        self, **kwargs: Any,
    ) -> Iterator[tuple[SummaryVariant, list[FamilyVariant]]]:
        pass

    def family_variants_iterator(
            self, **kwargs: Any) -> Iterator[FamilyVariant]:
        for _, variants in self.full_variants_iterator(**kwargs):
            yield from variants

    def summary_variants_iterator(
            self, **kwargs: Any) -> Iterator[SummaryVariant]:
        """Create a generator to iterate over summary variants."""
        for sv, fvs in self.full_variants_iterator(**kwargs):
            seen_in_status = sv.allele_count * [0]
            seen_as_denovo = sv.allele_count * [False]
            family_variants_count = sv.allele_count * [0]

            for fv in fvs:
                for aa in fv.alt_alleles:
                    fa = cast(FamilyAllele, aa)
                    seen_in_status[fa.allele_index] = reduce(
                        lambda t, s: t | s.value,
                        filter(None, fa.allele_in_statuses),
                        seen_in_status[fa.allele_index])
                    seen_as_denovo[fa.allele_index] = reduce(
                        lambda t, s: t or (s == Inheritance.denovo),
                        filter(None, fa.inheritance_in_members),
                        seen_as_denovo[fa.allele_index])
                    family_variants_count[fa.allele_index] += 1
            sv.update_attributes({
                "seen_in_status": seen_in_status[1:],
                "seen_as_denovo": seen_as_denovo[1:],
                "family_variants_count": family_variants_count[1:],
                "family_alleles_count": family_variants_count[1:],
            })
            yield sv

    @staticmethod
    def filter_regions(
        v: SummaryVariant, regions: list[Region],
    ) -> bool:
        """Return True if v is in regions."""
        pos = v.position
        assert pos is not None

        end_pos = v.end_position if v.end_position is not None else v.position

        for reg in regions:
            if reg.chrom != v.chromosome:
                continue
            if reg.start is None and reg.stop is None:
                return True
            if reg.start is None:
                assert reg.stop is not None
                if pos <= reg.stop:
                    return True
            if reg.stop is None:
                assert reg.start is not None
                if end_pos >= reg.start:
                    return True
            if reg.start is not None and reg.stop is not None:
                assert reg.start <= reg.stop
                if (reg.start <= pos <= reg.stop
                    or reg.start <= end_pos <= reg.stop
                    or (reg.start >= pos and reg.stop <= end_pos)
                ):
                    return True
        return False

    @staticmethod
    def filter_real_attr(
        allele: SummaryAllele,
        real_attr_filter: RealAttrFilterType, *,
        is_frequency: bool = False,
    ) -> bool:
        # pylint: disable=unused-argument
        """Return True if allele's attrs are within bounds.

        The bounds are specified in real_attr_filter.
        """
        result = []
        for key, ranges in real_attr_filter:
            if not allele.has_attribute(key):
                return False

            val = allele.get_attribute(key)
            rmin, rmax = ranges
            if rmin is None and rmax is None:
                if is_frequency or val is not None:
                    result.append(True)
            elif rmin is None:
                if is_frequency and val is None:
                    result.append(True)
                elif val is not None:
                    result.append(val <= rmax)
            elif rmax is None:
                result.append(val is not None and val >= rmin)
            else:
                result.append(
                    val is not None and (rmin <= val <= rmax))
        return all(result)

    @staticmethod
    def filter_gene_effects(
        v: SummaryAllele,
        effect_types: Sequence[str] | None,
        genes: Sequence[str] | None,
    ) -> bool:
        """Return True if variant's effects are in effect types and genes."""
        assert effect_types is not None or genes is not None
        if v.effects is None:
            return False

        gene_effects = v.effects.genes

        if effect_types is None:
            assert genes is not None
            result = [ge for ge in gene_effects if ge.symbol in genes]
            if result:
                v.matched_gene_effects = result
                return True
        elif genes is None:
            result = [ge for ge in gene_effects if ge.effect in effect_types]
            if result:
                v.matched_gene_effects = result
                return True
        else:
            result = [
                ge
                for ge in gene_effects
                if ge.effect in effect_types and ge.symbol in genes
            ]
            if result:
                v.matched_gene_effects = result
                return True
        return False

    @classmethod
    def filter_allele(  # noqa: C901
        cls,
        allele: FamilyAllele, *,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        person_ids: Sequence[str] | None = None,
        inheritance: Sequence[Matcher] | None = None,
        roles: Matcher | None = None,
        sexes: Matcher | None = None,
        affected_statuses: Matcher | None = None,
        variant_type: Matcher | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        **kwargs: Any,  # noqa: ARG003
    ) -> bool:
        # pylint: disable=too-many-arguments,too-many-return-statements
        # pylint: disable=too-many-branches,unused-argument
        """Return True if a family allele meets the required conditions."""
        assert isinstance(allele, FamilyAllele)
        if inheritance is not None:
            for inh in inheritance:
                if not inh.match(allele.inheritance_in_members):
                    return False

        if real_attr_filter is not None and \
                not cls.filter_real_attr(allele, real_attr_filter):
            return False
        if frequency_filter is not None and \
                not cls.filter_real_attr(
                    allele, frequency_filter, is_frequency=True):
            return False
        if ultra_rare and not cls.filter_real_attr(
                allele, [("af_allele_count", (None, 1))], is_frequency=True):
            return False

        if genes is None and effect_types is None:
            allele.matched_gene_effects = []
        elif not cls.filter_gene_effects(allele, effect_types, genes):
            return False
        if variant_type is not None and not variant_type.match(
                [allele.allele_type]):
            return False
        if person_ids is not None:
            if allele.is_reference_allele:
                return False
            if not set(allele.variant_in_members) & set(person_ids):
                return False
        if roles is not None:
            if allele.is_reference_allele:
                return False
            if not roles.match(allele.variant_in_roles):
                return False
        if sexes is not None:
            if allele.is_reference_allele:
                return False
            if not sexes.match(allele.variant_in_sexes):
                return False
        if affected_statuses is not None:
            if allele.is_reference_allele:
                return False
            if not affected_statuses.match(allele.variant_in_statuses):
                return False
        return True

    @classmethod
    def filter_summary_allele(
        cls,
        allele: SummaryAllele, *,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: Matcher | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        **kwargs: Any,  # noqa: ARG003
    ) -> bool:
        # pylint: disable=too-many-return-statements,too-many-branches
        # pylint: disable=unused-argument
        """Return True if a summary allele meets the required conditions."""
        assert isinstance(allele, SummaryAllele)
        if real_attr_filter is not None and \
                not cls.filter_real_attr(allele, real_attr_filter):
            return False
        if frequency_filter is not None and \
                not cls.filter_real_attr(
                    allele, frequency_filter, is_frequency=True):
            return False
        if ultra_rare and not cls.filter_real_attr(
                allele, [("af_allele_count", (0, 1))]):
            return False

        if (genes is not None or effect_types is not None) and \
                not cls.filter_gene_effects(allele, effect_types, genes):
            return False
        if variant_type is not None:
            return variant_type.match([allele.allele_type])

        return True

    @classmethod
    def filter_family_variant(
        cls, v: FamilyVariant, **kwargs: Any,
    ) -> bool:
        """Return true if variant meets conditions in kwargs."""
        if kwargs.get("regions") is not None and \
                not cls.filter_regions(v, kwargs["regions"]):
            return False
        family_ids = kwargs.get("family_ids")
        if family_ids is not None and v.family_id not in family_ids:
            return False
        if "filter" in kwargs:
            func = kwargs["filter"]
            if not func(v):
                return False
        return True

    @classmethod
    def filter_summary_variant(
        cls, v: SummaryVariant, **kwargs: Any,
    ) -> bool:
        """Return true if variant meets conditions in kwargs."""
        if kwargs.get("regions") is not None and \
                not cls.filter_regions(v, kwargs["regions"]):
            return False
        if "filter" in kwargs:
            func = kwargs["filter"]
            if not func(v):
                return False
        return True

    @classmethod
    def summary_variant_filter_function(
        cls, **kwargs: Any,
    ) -> Callable[[SummaryVariant], SummaryVariant | None]:
        """Return a filter function that checks the conditions in kwargs."""
        if kwargs.get("variant_type") is not None:
            parsed = kwargs["variant_type"]
            if isinstance(kwargs["variant_type"], str):
                parsed = variant_type_query.transform_query_string_to_tree(
                    parsed,
                )
            kwargs[
                "variant_type"
            ] = variant_type_query.transform_tree_to_matcher(parsed)

        return_reference = kwargs.get("return_reference", False)
        seen = kwargs.get("seen", set())

        def filter_func(sv: SummaryVariant) -> SummaryVariant | None:
            if sv is None:
                return None
            if sv.svuid in seen:
                return None
            seen.add(sv.svuid)

            if not cls.filter_summary_variant(sv, **kwargs):
                return None

            alleles = sv.alleles
            alleles_matched = []
            for allele in alleles:
                if cls.filter_summary_allele(allele, **kwargs):
                    if allele.allele_index == 0 and not return_reference:
                        continue
                    alleles_matched.append(allele.allele_index)
            if not alleles_matched:
                return None
            sv.set_matched_alleles(alleles_matched)
            return sv

        return filter_func

    @classmethod
    def summary_variant_filter_duplicate_function(
        cls, **kwargs: Any,
    ) -> Callable[[SummaryVariant], SummaryVariant | None]:
        """Return a filter function that checks the conditions in kwargs."""
        seen = kwargs.get("seen", set())

        def filter_func(sv: SummaryVariant) -> SummaryVariant | None:
            if sv is None:
                return None
            if sv.svuid in seen:
                return None

            seen.add(sv.svuid)
            return sv

        return filter_func

    def build_summary_variants_query_runner(
        self, **kwargs: Any,
    ) -> RawVariantsQueryRunner:
        """Return a query runner for the summary variants."""
        filter_func = RawFamilyVariants\
            .summary_variant_filter_function(**kwargs)
        return RawVariantsQueryRunner(
            variants_iterator=self.summary_variants_iterator(),
            deserializer=filter_func)

    def query_summary_variants(
        self, **kwargs: Any,
    ) -> Iterator[SummaryVariant]:
        """Run a sammary variant query and yields the results."""
        runner = self.build_summary_variants_query_runner(**kwargs)

        result = QueryResult(
            runners=[runner],
            limit=kwargs.get("limit", -1),
        )

        try:
            logger.debug("starting result")
            result.start()
            seen = set()
            with closing(result) as result:
                for sv in result:
                    if sv is None:
                        continue
                    if sv.svuid in seen:
                        continue
                    seen.add(sv.svuid)
                    yield sv
        finally:
            pass

    @classmethod
    def family_variant_filter_duplicate_function(
        cls, **kwargs: Any,
    ) -> Callable[[FamilyVariant], FamilyVariant | None]:
        """Return a filter function that checks the conditions in kwargs."""
        seen = kwargs.get("seen", set())

        def filter_func(fv: FamilyVariant) -> FamilyVariant | None:
            if fv is None or fv.fvuid in seen:
                return None
            seen.add(fv.fvuid)
            return fv

        return filter_func

    @classmethod
    def family_variant_filter_function(
        cls, **kwargs: Any,
    ) -> Callable[[FamilyVariant], FamilyVariant | None]:
        """Return a function that filters variants."""
        kwargs = cls._transform_family_variants_kwargs(kwargs)

        return_reference = kwargs.get("return_reference", False)
        return_unknown = kwargs.get("return_unknown", False)
        seen = kwargs.get("seen", set())

        def filter_func(v: FamilyVariant) -> FamilyVariant | None:
            try:
                if v is None or v.fvuid in seen:
                    return None
                seen.add(v.fvuid)

                if v.is_unknown() and not return_unknown:
                    logger.error(
                        "unknown variants selected but not requested %s", v)
                    return None

                if not cls.filter_family_variant(v, **kwargs):
                    logger.info(
                        "family variants selected but not requested %s", v)
                    return None

                alleles = v.alleles
                alleles_matched = []
                for allele in alleles:
                    if allele.allele_index == 0 and not return_reference:
                        continue
                    fa = cast(FamilyAllele, allele)
                    if cls.filter_allele(fa, **kwargs):
                        alleles_matched.append(allele.allele_index)
                if alleles_matched:
                    v.set_matched_alleles(alleles_matched)
                    return v
                logger.info("no matched alleles for family variant: %s", v)
            except Exception as ex:  # pylint: disable=broad-except  # noqa: BLE001
                logger.warning(
                    "unexpected error: %s; %s", ex, v, exc_info=True)
                return None
            return None

        return filter_func

    @classmethod
    def _transform_family_variants_kwargs(
        cls, kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        if kwargs.get("roles") is not None:
            parsed = kwargs["roles"]
            if isinstance(parsed, list):
                parsed = f"any({','.join(parsed)})"
            if isinstance(parsed, str):
                parsed = role_query.transform_query_string_to_tree(parsed)

            kwargs["roles"] = role_query.transform_tree_to_matcher(parsed)

        if kwargs.get("sexes") is not None:
            parsed = kwargs["sexes"]
            if isinstance(parsed, str):
                parsed = sex_query.transform_query_string_to_tree(parsed)

            kwargs["sexes"] = sex_query.transform_tree_to_matcher(parsed)

        if kwargs.get("affected_statuses") is not None:
            parsed = kwargs["affected_statuses"]
            if isinstance(parsed, str):
                parsed = affected_status_query\
                    .transform_query_string_to_tree(parsed)

            kwargs["affected_statuses"] = affected_status_query\
                .transform_tree_to_matcher(parsed)

        if kwargs.get("inheritance") is not None:
            parsed = kwargs["inheritance"]
            if isinstance(parsed, str):
                parsed = [
                    inheritance_query.transform_query_string_to_tree(parsed),
                ]
            elif isinstance(parsed, list):
                parsed = [
                    inheritance_query.transform_query_string_to_tree(p)
                    for p in parsed
                ]

            kwargs["inheritance"] = [
                inheritance_query.transform_tree_to_matcher(p)
                for p in parsed
            ]

        if kwargs.get("variant_type") is not None:
            parsed = kwargs["variant_type"]
            if isinstance(kwargs["variant_type"], str):
                parsed = variant_type_query.transform_query_string_to_tree(
                    parsed,
                )

            kwargs[
                "variant_type"
            ] = variant_type_query.transform_tree_to_matcher(parsed)

        return kwargs

    def build_family_variants_query_runner(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: Sequence[str] | None = None,
        person_ids: Sequence[str] | None = None,
        inheritance: Sequence[str] | None = None,
        roles_in_parent: str | None = None,
        roles_in_child: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        tags_query: TagsQuery | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> RawVariantsQueryRunner:
        # pylint: disable=too-many-arguments,unused-argument
        """Return a query runner for the family variants."""
        # In memory variants does not inherit QueryVariantsBase,
        # but is suitable for the tags to family IDs utility.
        roles = QueryVariantsBase.transform_roles_to_single_role_string(
                roles_in_parent, roles_in_child,
        )
        tag_family_ids = QueryVariantsBase.tags_to_family_ids(
            self, tags_query,  # type: ignore
        )
        if tag_family_ids is not None:
            if family_ids is not None:
                family_ids = list(set(family_ids).intersection(tag_family_ids))
            else:
                family_ids = list(tag_family_ids)
        filter_func = RawFamilyVariants.family_variant_filter_function(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            affected_statuses=affected_statuses,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown)

        return RawVariantsQueryRunner(
            variants_iterator=self.family_variants_iterator(),
            deserializer=filter_func)

    def query_variants(self, **kwargs: Any) -> Iterator[FamilyVariant]:
        """Query family variants and yield the results."""
        runner = self.build_family_variants_query_runner(**kwargs)

        result = QueryResult(
            runners=[runner],
            limit=kwargs.get("limit", -1),
        )

        try:
            logger.debug("starting result")
            result.start()
            seen = set()
            with closing(result) as result:
                for v in result:
                    if v is None:
                        continue
                    if v.fvuid in seen:
                        continue
                    seen.add(v.fvuid)
                    yield v
        finally:
            pass


class RawMemoryVariants(RawFamilyVariants):
    """Store variants in memory."""

    def __init__(
        self, full_variants: list[tuple[SummaryVariant, list[FamilyVariant]]],
        families: FamiliesData,
    ) -> None:
        super().__init__(families)
        self._full_variants = full_variants

    def has_affected_status_queries(self) -> bool:
        return False

    @property
    def full_variants(
        self,
    ) -> list[tuple[SummaryVariant, list[FamilyVariant]]]:
        """Return the full list of variants."""
        return self._full_variants

    def full_variants_iterator(
        self, **_kwargs: Any,
    ) -> Iterator[tuple[SummaryVariant, list[FamilyVariant]]]:
        yield from self.full_variants
