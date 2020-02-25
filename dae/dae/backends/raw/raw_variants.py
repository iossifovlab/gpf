import sys
import time

from dae.variants.family_variant import FamilyAllele

from dae.backends.attributes_query import (
    role_query,
    sex_query,
    inheritance_query,
    variant_type_query,
)


class RawFamilyVariants:
    def __init__(self, families):
        self.families = families

    def full_variants_iterator(self):
        raise NotImplementedError()

    @staticmethod
    def filter_regions(v, regions):
        for reg in regions:
            if reg.chr == v.chromosome and reg.start <= v.position <= reg.stop:
                return True
        return False

    @staticmethod
    def filter_real_attr(va, real_attr_filter):
        result = []
        for key, ranges in real_attr_filter:
            if not va.has_attribute(key):
                return False

            val = va.get_attribute(key)
            if val is None:
                continue
            rmin, rmax = ranges
            if rmin is None:
                result.append(val <= rmax)
            elif rmax is None:
                result.append(val >= rmin)
            else:
                result.append((val >= rmin) and (val <= rmax))
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
        ultra_rare=None,
        genes=None,
        effect_types=None,
        variant_type=None,
        person_ids=None,
        roles=None,
        sexes=None,
        **kwargs,
    ):

        assert isinstance(allele, FamilyAllele)
        if inheritance is not None:
            # if v.is_reference_allele:
            #     return False
            if not inheritance.match(allele.inheritance_in_members):
                return False

        if real_attr_filter is not None:
            if not cls.filter_real_attr(allele, real_attr_filter):
                return False
        if ultra_rare:
            if not cls.filter_real_attr(allele, [("af_allele_count", (1, 1))]):
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
    def filter_variant(cls, v, **kwargs):
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

    def query_variants(self, **kwargs):
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
                parsed = inheritance_query.transform_query_string_to_tree(
                    parsed
                )

            kwargs[
                "inheritance"
            ] = inheritance_query.transform_tree_to_matcher(parsed)

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

        for _, vs in self.full_variants_iterator():
            for v in vs:
                if v.is_unknown() and not return_unknown:
                    continue

                if not self.filter_variant(v, **kwargs):
                    continue

                alleles = v.alleles
                alleles_matched = []
                for allele in alleles:
                    if self.filter_allele(allele, **kwargs):
                        if allele.allele_index == 0 and not return_reference:
                            continue
                        alleles_matched.append(allele.allele_index)
                if alleles_matched:
                    v.set_matched_alleles(alleles_matched)
                    yield v


class RawMemoryVariants(RawFamilyVariants):
    def __init__(self, loaders):
        assert len(loaders) > 0
        super(RawMemoryVariants, self).__init__(loaders[0].families)
        self.variants_loaders = loaders
        self._full_variants = None

    @property
    def full_variants(self):
        if self._full_variants is None:
            start = time.time()
            self._full_variants = []
            for loader in self.variants_loaders:
                for sv, fvs in loader.full_variants_iterator():
                    self._full_variants.append((sv, fvs))

            elapsed = time.time() - start
            print(f"Variants loaded in in {elapsed:.2f} sec", file=sys.stderr)
        return self._full_variants

    def full_variants_iterator(self):
        for sv, fvs in self.full_variants:
            yield sv, fvs
