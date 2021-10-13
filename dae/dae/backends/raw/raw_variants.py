import time
import logging
import queue
import abc

from contextlib import closing

from dae.variants.variant import SummaryAllele
from dae.variants.family_variant import FamilyAllele

from dae.backends.query_runners import QueryRunner, QueryResult
from dae.backends.attributes_query import (
    role_query,
    sex_query,
    inheritance_query,
    variant_type_query,
)


logger = logging.getLogger(__name__)


class RawVariantsQueryRunner(QueryRunner):

    def __init__(
            self, variants_iterator=None,
            deserializer=None):
        super(RawVariantsQueryRunner, self).__init__(
            deserializer=deserializer)
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

        except BaseException as ex:
            logger.warn(
                f"exception in runner run: {type(ex)}", exc_info=True)
        finally:
            self.close()

        with self._status_lock:
            self._done = True
        logger.debug("raw variants query runner done")


class RawFamilyVariants(abc.ABC):

    def __init__(self, families):
        self.families = families

    @abc.abstractmethod
    def full_variants_iterator(self):
        pass

    def family_variants_iterator(self):
        for _, vs in self.full_variants_iterator():
            for v in vs:
                yield v

    def summary_variants_iterator(self):
        for sv, _ in self.full_variants_iterator():
            yield sv

    @staticmethod
    def filter_regions(v, regions):
        if v.end_position is None:
            end_position = -1
        else:
            end_position = v.end_position

        for reg in regions:
            if (
                reg.chrom == v.chromosome
                and (
                    reg.start <= v.position <= reg.stop or
                    reg.start <= end_position <= reg.stop or
                    (reg.start >= v.position and reg.stop <= end_position)
                )
            ):
                return True
        return False

    @staticmethod
    def filter_real_attr(va, real_attr_filter, is_frequency=False):
        result = []
        for key, ranges in real_attr_filter:
            if not va.has_attribute(key):
                return False

            val = va.get_attribute(key)
            rmin, rmax = ranges
            if rmin is None and rmax is None:
                result.append(True)
            elif rmin is None:
                result.append(val is None or val <= rmax)
            elif rmax is None:
                result.append(val is not None and val >= rmin)
            else:
                result.append(
                    val is not None and (val >= rmin) and (val <= rmax))
        if all(result):
            return True

        return False

    @staticmethod
    def filter_gene_effects(v, effect_types, genes):
        assert effect_types is not None or genes is not None
        if v.effect is None:
            return False

        gene_effects = v.effect.genes

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
    def filter_allele(
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
            **kwargs):

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
            if not variant_type.match([allele.variant_type]):
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
            **kwargs):

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
            if not variant_type.match([allele.variant_type]):
                return False
        if person_ids is not None:
            if allele.is_reference_allele:
                return False
            if not set(allele.variant_in_members) & set(person_ids):
                return False
        return True

    @classmethod
    def filter_family_variant(cls, v, **kwargs):
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
            else:
                sv.set_matched_alleles(alleles_matched)
                return sv

        return filter_func

    def build_summary_variants_query_runner(self, **kwargs):
        filter_func = RawFamilyVariants\
            .summary_variant_filter_function(**kwargs)
        runner = RawVariantsQueryRunner(
            variants_iterator=self.summary_variants_iterator(),
            deserializer=filter_func)

        return runner

    def query_summary_variants(self, **kwargs):
        runner = self.build_summary_variants_query_runner(**kwargs)

        result = QueryResult(
                runners=[runner],
                limit=kwargs.get("limit", -1))

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
    def family_variant_filter_function(cls, **kwargs):
        if kwargs.get("roles") is not None:
            parsed = kwargs["roles"]
            if isinstance(parsed, list):
                parsed = "any({})".format(",".join(parsed))
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
                    if cls.filter_allele(allele, **kwargs):
                        if allele.allele_index == 0 and not return_reference:
                            continue
                        alleles_matched.append(allele.allele_index)
                if alleles_matched:
                    v.set_matched_alleles(alleles_matched)
                    return v
            except Exception as ex:
                logger.warning(f"unexpected error: {ex}", exc_info=True)
                return None

        return filter_func

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
            affected_status=None):

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
        runner = self.build_family_variants_query_runner(**kwargs)

        result = QueryResult(
                runners=[runner],
                limit=kwargs.get("limit", -1))

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
    def __init__(self, loaders, families):
        super(RawMemoryVariants, self).__init__(families)
        self.variants_loaders = loaders
        if len(loaders) > 0:
            self._full_variants = None
        else:
            logger.debug("no variants to load")
            self._full_variants = []

    @property
    def full_variants(self):
        if self._full_variants is None:
            start = time.time()
            self._full_variants = []
            for loader in self.variants_loaders:
                for sv, fvs in loader.full_variants_iterator():
                    self._full_variants.append((sv, fvs))

            elapsed = time.time() - start
            logger.debug(f"variants loaded in in {elapsed:.2f} sec")
        return self._full_variants

    def full_variants_iterator(self):
        for sv, fvs in self.full_variants:
            yield sv, fvs
