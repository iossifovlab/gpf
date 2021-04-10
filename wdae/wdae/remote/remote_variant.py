from typing import List

from dae.variants.variant import SummaryAllele, SummaryVariant

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

    def __init__(self, columns: List[str], attributes_list: list):
        # columns is an ordered list of columns by their source name
        self.columns = columns
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


class RemoteVariant(SummaryVariant):

    def __init__(self, columns: List[str], alleles_list: list):
        # columns is an ordered list of columns by their source name
        self.columns = columns
        self.alleles_list = alleles_list
        remote_alleles = [RemoteAllele(columns, a) for a in self.alleles_list]
        ref_allele = RemoteAllele.create_reference_allele(remote_alleles[0])
        remote_alleles.insert(0, ref_allele)
        super(RemoteVariant, self).__init__(remote_alleles)
