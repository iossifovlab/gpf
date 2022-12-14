import math
from copy import copy
from typing import List, Optional, cast

from dae.variants.variant import SummaryAllele, SummaryVariant

from dae.variants.family_variant import FamilyAllele, FamilyVariant

from dae.pedigrees.family import Family

from dae.utils.variant_utils import str2mat, str2fgt

SUMMARY_QUERY_SOURCES = [
    {"source": "chrom"},
    {"source": "position"},
    {"source": "end_position"},
    {"source": "reference"},
    {"source": "alternative"},
    {"source": "summary_index"},
    {"source": "allele_index"},
    {"source": "transmission_type"},
    {"source": "raw_effects"},
    {"source": "effect_types"},
    {"source": "effect_genes"},
    {"source": "effect_gene_symbols"},
    {"source": "frequency"},
]

SUMMARY_COLUMNS = [s["source"] for s in SUMMARY_QUERY_SOURCES]

FAMILY_QUERY_SOURCES = [
    {"source": "family"},
    {"source": "genotype"},
    {"source": "best_st"},
    {"source": "genetic_model"},
]

FAMILY_COLUMNS = [s["source"] for s in FAMILY_QUERY_SOURCES]

QUERY_SOURCES = [
    *SUMMARY_QUERY_SOURCES,
    *FAMILY_QUERY_SOURCES
]

COLUMNS = [
    *SUMMARY_COLUMNS,
    *FAMILY_COLUMNS
]


class RemoteAllele(SummaryAllele):

    def __init__(
        self,
        attributes_list: List,
        idx: int,
        columns: Optional[List[str]] = None
    ):
        # columns is an ordered list of columns by their source name
        self.columns = columns if columns else SUMMARY_COLUMNS
        self.attributes_list = attributes_list
        self.idx = idx

        end_position = self._find_attribute("end_position")
        end_position = int(end_position) \
            if end_position is not None and \
            not math.isnan(float(end_position)) \
            else None

        super(RemoteAllele, self).__init__(
            self._find_attribute("chrom"),
            int(self._find_attribute("position")),
            self._find_attribute("reference"),
            alternative=self._find_attribute("alternative"),
            end_position=end_position,
            summary_index=self._find_attribute("summary_index"),
            allele_index=self._find_attribute("allele_index"),
            effect=self._find_attribute("raw_effects"),
            attributes={col: self._find_attribute(col) for col in self.columns}
        )

    def _find_attribute(self, source: str):
        if source not in self.columns:
            return None
        attr = self.attributes_list[self.columns.index(source)][self.idx]
        return attr if attr != "-" else None

    @staticmethod
    def create_reference_allele(allele) -> "RemoteAllele":
        new_attributes = copy(allele.attributes_list)
        new_attributes[allele.columns.index("allele_index")][0] = 0
        new_attributes[allele.columns.index("alternative")][0] = None
        return RemoteAllele(new_attributes, 0, allele.columns)


class RemoteFamilyAllele(FamilyAllele):
    def __init__(
        self,
        attributes_list: List,
        idx: int,
        family: Family,
        columns: Optional[List[str]] = None
    ):
        self.columns = columns if columns else SUMMARY_COLUMNS
        self.attributes_list = attributes_list
        self.idx = idx
        summary_allele = RemoteAllele(attributes_list, idx, self.columns)
        genotype = self._find_attribute("genotype")
        best_state = self._find_attribute("best_st")
        genetic_model = self._find_attribute("genetic_model")
        super().__init__(
            summary_allele, family, genotype, best_state, genetic_model
        )

    def _find_attribute(self, source: str):
        if source not in self.columns:
            return None
        attr = self.attributes_list[self.columns.index(source)][self.idx]
        return attr if attr != "-" else None

    @property
    def inheritance_in_members(self):
        # TODO Implement this
        return []


class RemoteVariant(SummaryVariant):

    def __init__(
        self,
        attributes_list: List,
        columns: Optional[List[str]] = None,
    ):
        # columns is an ordered list of columns by their source name
        self.columns = columns if columns else SUMMARY_COLUMNS
        self.attributes_list = attributes_list
        allele_count = len(self.attributes_list[0])
        remote_alleles = []
        for idx in range(allele_count):
            remote_alleles.append(
                RemoteAllele(self.attributes_list, idx, self.columns)
            )
        ref_allele = RemoteAllele.create_reference_allele(remote_alleles[0])
        remote_alleles.insert(0, ref_allele)
        super().__init__(cast(List[SummaryAllele], remote_alleles))


class RemoteFamilyVariant(FamilyVariant):
    def __init__(
        self,
        attributes_list: List,
        family: Family,
        columns: Optional[List[str]] = None,
    ):
        self.columns = columns if columns else SUMMARY_COLUMNS

        self.attributes_list = attributes_list
        allele_count = len(self.attributes_list[0])
        remote_alleles = []
        for idx in range(allele_count):
            remote_alleles.append(RemoteFamilyAllele(
                self.attributes_list, idx, family, self.columns
            ))
        genotype = remote_alleles[0]._find_attribute("genotype")
        best_state = remote_alleles[0]._find_attribute("best_st")
        self.summary_variant = RemoteVariant(
            copy(self.attributes_list), self.columns
        )
        ref_allele = RemoteAllele.create_reference_allele(remote_alleles[0])
        remote_alleles.insert(0, ref_allele)

        self._remote_alleles = remote_alleles

        super().__init__(
            self.summary_variant, family,
            str2fgt(genotype), str2mat(best_state)
        )

    @property
    def alt_alleles(self):
        return self._remote_alleles[1:]

    @property
    def family_genotype(self):
        return self.gt.transpose()
