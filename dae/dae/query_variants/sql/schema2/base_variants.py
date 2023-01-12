import logging
import abc
import configparser

from typing import Optional

import pandas as pd

from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader

logger = logging.getLogger(__name__)


class SqlSchema2Variants(abc.ABC):
    """Base class for Schema2 SQL like variants' query interface."""

    def __init__(
            self,
            dialect,
            db,
            family_variant_table,
            summary_allele_table,
            pedigree_table,
            meta_table,
            gene_models=None):
        assert db
        assert pedigree_table

        self.dialect = dialect
        self.db = db
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.pedigree_table = pedigree_table
        self.meta_table = meta_table
        self.gene_models = gene_models

        self.summary_allele_schema = self._fetch_schema(
            self.summary_allele_table
        )
        self.family_variant_schema = self._fetch_schema(
            self.family_variant_table
        )
        self.combined_columns = {
            **self.family_variant_schema,
            **self.summary_allele_schema,
        }

        self.pedigree_schema = self._fetch_schema(self.pedigree_table)
        self.ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.ped_df)
        # Temporary workaround for studies that are imported without tags
        FamiliesLoader._build_families_tags(
            self.families, {"ped_tags": True}
        )

        _tbl_props = self._fetch_tblproperties()
        self.table_properties = self._normalize_tblproperties(_tbl_props)

    @abc.abstractmethod
    def _fetch_schema(self, table) -> dict[str, str]:
        """Fetch schema of a table and return it as a Dict."""

    @abc.abstractmethod
    def _fetch_pedigree(self) -> pd.DataFrame:
        """Fetch the pedigree and return it as a data frame."""

    @abc.abstractmethod
    def _fetch_tblproperties(self) -> Optional[configparser.ConfigParser]:
        """Fetch partion description from metadata table."""

    @staticmethod
    def _normalize_tblproperties(tbl_props) -> dict:
        if tbl_props is None:
            return {
                "region_length": 0,
                "chromosomes": [],
                "family_bin_size": 0,
                "coding_effect_types": set(),
                "rare_boundary": 0
            }

        return {
            "region_length": int(
                tbl_props["region_bin"]["region_length"]
            ),
            "chromosomes": [
                c.strip()
                for c in tbl_props["region_bin"]["chromosomes"].split(",")
            ],
            "family_bin_size": int(
                tbl_props["family_bin"]["family_bin_size"]
            ),
            "rare_boundary": int(
                tbl_props["frequency_bin"]["rare_boundary"]
            ),
            "coding_effect_types": set(
                s.strip()
                for s in tbl_props["coding_bin"][
                    "coding_effect_types"
                ].split(",")
            ),
        }
