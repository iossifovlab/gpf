from typing import List

from dae.variants.variant import SummaryAllele, SummaryVariant

from dae.variants.family_variant import FamilyAllele, FamilyVariant

from remote.family import RemoteFamily

SUMMARY_QUERY_SOURCES = [
    {"source": "chromosome"},
    {"source": "position"},
    {"source": "end_position"},
    {"source": "reference"},
    {"source": "alternative"},
    {"source": "summary_index"},
    {"source": "allele_index"},
    {"source": "transmission_type"},
    {"source": "effect"},
    {"source": "effect_types"},
    {"source": "effect_genes"},
    {"source": "effect_gene_symbols"},
    {"source": "frequency"},
]

SUMMARY_COLUMNS = [s["source"] for s in SUMMARY_QUERY_SOURCES]

FAMILY_QUERY_SOURCES = [
    {"source": "family_id"},
    {"source": "genotype"},
    {"source": "best_state"},
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

    def __init__(self, attributes_list: List):
        # columns is an ordered list of columns by their source name
        self.columns = SUMMARY_COLUMNS
        self.attributes_list = list(map(
            lambda v: v[0] if isinstance(v, list) and len(v) == 1 else v,
            attributes_list
        ))

        end_position = self._find_attribute("end_position")
        end_position = int(end_position) \
            if end_position is not None else None

        super(RemoteAllele, self).__init__(
            self._find_attribute("chromosome"),
            int(self._find_attribute("position")),
            self._find_attribute("reference"),
            alternative=self._find_attribute("alternative"),
            end_position=end_position,
            summary_index=self._find_attribute("summary_index"),
            allele_index=self._find_attribute("allele_index"),
            attributes=dict(zip(self.columns, self.attributes_list))
        )

    def _find_attribute(self, source: str):
        if source not in self.columns:
            return None
        return self.attributes_list[self.columns.index(source)]

    @staticmethod
    def create_reference_allele(allele) -> "RemoteAllele":
        new_attributes = list(allele.attributes_list)
        new_attributes[allele.columns.index("alternative")] = None
        return RemoteAllele(allele.columns, new_attributes)


class RemoteFamilyAllele(FamilyAllele):
    def __init__(
        self, attributes_list: List, family: RemoteFamily
    ):
        self.columns = COLUMNS
        self.attributes_list = attributes_list
        summary_allele = RemoteAllele(attributes_list)
        genotype = self._find_attribute("genotype")
        best_state = self._find_attribute("best_state")
        genetic_model = self._find_attribute("genetic_model")
        super().__init__(
            summary_allele, family, genotype, best_state, genetic_model
        )

    def _find_attribute(self, source: str):
        if source not in self.columns:
            return None
        return self.attributes_list[self.columns.index(source)]


class RemoteVariant(SummaryVariant):

    def __init__(self, alleles_list: List):
        # columns is an ordered list of columns by their source name
        self.columns = SUMMARY_COLUMNS
        self.alleles_list = alleles_list
        remote_alleles = [RemoteAllele(a) for a in self.alleles_list]
        ref_allele = RemoteAllele.create_reference_allele(remote_alleles[0])
        remote_alleles.insert(0, ref_allele)
        super(RemoteVariant, self).__init__(remote_alleles)


class RemoteFamilyVariant(FamilyVariant):
    def __init__(
        self, alleles_list: List, family: RemoteFamily
    ):
        self.columns = COLUMNS
        self.alleles_list = alleles_list
        remote_alleles = [
            RemoteFamilyAllele(a, family) for a in self.alleles_list
        ]
        ref_allele = RemoteAllele.create_reference_allele(remote_alleles[0])
        remote_alleles.insert(0, ref_allele)
        super(RemoteVariant, self).__init__(remote_alleles)
