import time
import logging
import queue
import abc

from contextlib import closing

from dae.variants.variant import SummaryAllele
from dae.variants.family_variant import FamilyAllele

from dae.query_variants.query_runners import QueryRunner, QueryResult
from dae.query_variants.attributes_query import (
    role_query,
    sex_query,
    inheritance_query,
    variant_type_query,
)


logger = logging.getLogger(__name__)


class RawVariantsQueryRunner(QueryRunner):
    """Run a variant iterator as a query."""

    def __init__(
            self, variants_iterator=None,
            deserializer=None):
        super().__init__(deserializer=deserializer)
        self.variants_iterator = variants_iterator
        assert self.variants_iterator is not None

    def run(self):
        try:
            if self.closed():
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
                        self._result_queue.put(val, timeout=0.1)
                        break
                    except queue.Full:
                        if self.closed():
                            break

                if self.closed():
                    break

        except StopIteration:
            logger.debug("variants iterator done")

        except BaseException as ex:  # pylint: disable=broad-except
            logger.warning(
                "exception in runner run: %s", type(ex), exc_info=True)
        finally:
            self.close()

        with self._status_lock:
            self._done = True
        logger.debug("raw variants query runner done")


class RawFamilyVariants(abc.ABC):
    """Base class that stores a reference to the families data."""

    def __init__(self, families):
        self.families = families

    @abc.abstractmethod
    def full_variants_iterator(self):
        pass

    def family_variants_iterator(self):
        for _, variants in self.full_variants_iterator():
            for v in variants:
                yield v

    def summary_variants_iterator(self):
        for sv, _ in self.full_variants_iterator():
            yield sv

    @staticmethod
    def filter_regions(v, regions):
        """Return True if v is in regions."""
        if v.end_position is None:
            end_position = -1
        else:
            end_position = v.end_position

        for reg in regions:
            if (
                reg.chrom == v.chromosome
                and (
                    reg.start <= v.position <= reg.stop
                    or reg.start <= end_position <= reg.stop
                    or (reg.start >= v.position and reg.stop <= end_position)
                )
            ):
                return True
        return False

    @staticmethod
    def filter_real_attr(variant, real_attr_filter, is_frequency=False):
        # pylint: disable=unused-argument
        """Return True if variant's attrs are within bounds.

        The bounds are specified in real_attr_filter.
        """
        result = []
        for key, ranges in real_attr_filter:
            if not variant.has_attribute(key):
                return False

            val = variant.get_attribute(key)
            rmin, rmax = ranges
            if rmin is None and rmax is None:
                result.append(True)
            elif rmin is None:
                result.append(val is None or val <= rmax)
            elif rmax is None:
                result.append(val is not None and val >= rmin)
            else:
                result.append(
                    val is not None and (rmin <= val <= rmax))
        if all(result):
            return True

        return False

    @staticmethod
    def filter_gene_effects(v, effect_types, genes):
        """Return True if variant's effects are in effect types and genes."""
        assert effect_types is not None or genes is not None
        if v.effects is None:
            return False

        gene_effects = v.effects.genes

        if effect_types is None:
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
    def filter_allele(  # NOQA
            cls,
            allele,
            inheritance=None,
            real_attr_filter=None,
            frequency_filter=None,
            ultra_rare=None,
            genes=None,
            effect_types=None,
            variant_type=None,
            person_ids=None,
            roles=None,
            sexes=None,
            **_kwargs):
        # pylint: disable=too-many-arguments,too-many-return-statements
        # pylint: disable=too-many-branches
        """Return True if a family allele meets the required conditions."""
        assert isinstance(allele, FamilyAllele)
        if inheritance is not None:
            # if v.is_reference_allele:
            #     return False
            for inh in inheritance:
                if not inh.match(allele.inheritance_in_members):
                    return False

        if real_attr_filter is not None:
            if not cls.filter_real_attr(allele, real_attr_filter):
                return False
        if frequency_filter is not None:
            if not cls.filter_real_attr(
                    allele, frequency_filter, is_frequency=True):
                return False
        if ultra_rare:
            if not cls.filter_real_attr(
                    allele, [("af_allele_count", (None, 1))]):
                return False

        if genes is not None or effect_types is not None:
            if not cls.filter_gene_effects(allele, effect_types, genes):
                return False
        if variant_type is not None:
            if not variant_type.match([allele.allele_type]):
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
        return True

    @classmethod
    def filter_summary_allele(
            cls,
            allele,
            real_attr_filter=None,
            frequency_filter=None,
            ultra_rare=None,
            genes=None,
            effect_types=None,
            variant_type=None,
            person_ids=None,
            **_kwargs):
        # pylint: disable=too-many-return-statements,too-many-branches
        """Return True if a summary allele meets the required conditions."""
        assert isinstance(allele, SummaryAllele)
        if real_attr_filter is not None:
            if not cls.filter_real_attr(allele, real_attr_filter):
                return False
        if frequency_filter is not None:
            if not cls.filter_real_attr(
                    allele, frequency_filter, is_frequency=True):
                return False
        if ultra_rare:
            if not cls.filter_real_attr(allele, [("af_allele_count", (0, 1))]):
                return False

        if genes is not None or effect_types is not None:
            if not cls.filter_gene_effects(allele, effect_types, genes):
                return False
        if variant_type is not None:
            if not variant_type.match([allele.allele_type]):
                return False
        if person_ids is not None:
            if allele.is_reference_allele:
                return False
            if not set(allele.variant_in_members) & set(person_ids):
                return False
        return True

    @classmethod
    def filter_family_variant(cls, v, **kwargs):
        """Return true if variant meets conditions in kwargs."""
        if kwargs.get("regions") is not None:
            if not cls.filter_regions(v, kwargs["regions"]):
                return False
        if "family_ids" in kwargs and kwargs["family_ids"] is not None:
            family_ids = kwargs["family_ids"]
            if v.family_id not in family_ids:
                return False
        if "filter" in kwargs:
            func = kwargs["filter"]
            if not func(v):
                return False
        return True

    @classmethod
    def filter_summary_variant(cls, v, **kwargs):
        """Return true if variant meets conditions in kwargs."""
        if kwargs.get("regions") is not None:
            if not cls.filter_regions(v, kwargs["regions"]):
                return False
        if "filter" in kwargs:
            func = kwargs["filter"]
            if not func(v):
                return False
        return True

    @classmethod
    def summary_variant_filter_function(cls, **kwargs):
        """Return a filter function that checks the conditions in kwargs."""
        if kwargs.get("variant_type") is not None:
            parsed = kwargs["variant_type"]
            if isinstance(kwargs["variant_type"], str):
                parsed = variant_type_query.transform_query_string_to_tree(
                    parsed
                )
            kwargs[
                "variant_type"
            ] = variant_type_query.transform_tree_to_matcher(parsed)

        return_reference = kwargs.get("return_reference", False)

        def filter_func(sv):
            if sv is None:
                return None
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

    def build_summary_variants_query_runner(self, **kwargs):
        """Return a query runner for the summary variants."""
        filter_func = RawFamilyVariants\
            .summary_variant_filter_function(**kwargs)
        runner = RawVariantsQueryRunner(
            variants_iterator=self.summary_variants_iterator(),
            deserializer=filter_func)

        return runner

    def query_summary_variants(self, **kwargs):
        """Run a sammary variant query and yields the results."""
        runner = self.build_summary_variants_query_runner(**kwargs)

        result = QueryResult(
            runners=[runner],
            limit=kwargs.get("limit", -1)
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
    def family_variant_filter_function(cls, **kwargs):  # noqa
        """Return a function that filters variants."""
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

        if kwargs.get("inheritance") is not None:
            parsed = kwargs["inheritance"]
            if isinstance(parsed, str):
                parsed = [
                    inheritance_query.transform_query_string_to_tree(parsed)
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
                    parsed
                )

            kwargs[
                "variant_type"
            ] = variant_type_query.transform_tree_to_matcher(parsed)

        return_reference = kwargs.get("return_reference", False)
        return_unknown = kwargs.get("return_unknown", False)

        def filter_func(v):
            try:
                if v is None:
                    return None
                if v.is_unknown() and not return_unknown:
                    return None

                if not cls.filter_family_variant(v, **kwargs):
                    return None

                alleles = v.alleles
                alleles_matched = []
                for allele in alleles:
                    if allele.allele_index == 0 and not return_reference:
                        continue
                    if cls.filter_allele(allele, **kwargs):
                        alleles_matched.append(allele.allele_index)
                if alleles_matched:
                    v.set_matched_alleles(alleles_matched)
                    return v
                return None
            except Exception as ex:  # pylint: disable=broad-except
                logger.warning("unexpected error: %s", ex, exc_info=True)
                return None

        return filter_func

    @staticmethod
    def build_person_set_collection_query(
            person_set_collection, person_set_collection_query):
        # pylint: disable=unused-argument
        return None

    def build_family_variants_query_runner(
            self,
            regions=None,
            genes=None,
            effect_types=None,
            family_ids=None,
            person_ids=None,
            inheritance=None,
            roles=None,
            sexes=None,
            variant_type=None,
            real_attr_filter=None,
            ultra_rare=None,
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            limit=None,
            pedigree_fields=None):
        # pylint: disable=too-many-arguments,unused-argument
        """Return a query runner for the family variants."""
        filter_func = RawFamilyVariants.family_variant_filter_function(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit)

        runner = RawVariantsQueryRunner(
            variants_iterator=self.family_variants_iterator(),
            deserializer=filter_func)

        return runner

    def query_variants(self, **kwargs):
        """Query family variants and yield the results."""
        runner = self.build_family_variants_query_runner(**kwargs)

        result = QueryResult(
            runners=[runner],
            limit=kwargs.get("limit", -1)
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

    def __init__(self, loaders, families):
        super().__init__(families)
        self.variants_loaders = loaders
        if len(loaders) > 0:
            self._full_variants = None
        else:
            logger.debug("no variants to load")
            self._full_variants = []

    @property
    def full_variants(self):
        """Return the full list of variants."""
        if self._full_variants is None:
            start = time.time()
            self._full_variants = []
            for loader in self.variants_loaders:
                for sv, fvs in loader.full_variants_iterator():
                    self._full_variants.append((sv, fvs))

            elapsed = time.time() - start
            logger.debug("variants loaded in in %.2f sec", elapsed)
        return self._full_variants

    def full_variants_iterator(self):
        for sv, fvs in self.full_variants:
            yield sv, fvs
