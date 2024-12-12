import logging
from copy import copy
from typing import Any

from box import Box
import duckdb
import numpy as np
import sqlglot
from sqlalchemy import (  # type: ignore
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
)
from sqlalchemy.sql import insert, select

from dae.gene_profile.statistic import GPStatistic
from dae.utils.sql_utils import to_duckdb_transpile

logger = logging.getLogger(__name__)


class GeneProfileDB:
    """
    Class for managing the gene profile database.

    Uses SQLite for DB management and supports loading
    and storing to filesystem.
    Has to be supplied a configuration and a path to which to read/write
    the SQLite DB.
    """

    PAGE_SIZE = 50

    def __init__(
        self,
        configuration: Box | None,
        dbfile: str,
        clear: bool = False,
    ):
        self.dbfile = dbfile
        self.engine = create_engine(f"sqlite:///{dbfile}")
        duckdb.execute("INSTALL sqlite;")
        duckdb.execute("LOAD sqlite;")
        self.metadata = MetaData()
        self.configuration = \
            GeneProfileDB.build_configuration(configuration)
        self._create_gp_table()
        self.gene_sets_categories = {}
        if clear:
            self._clear_gp_table()
        if len(self.configuration.keys()):
            for category in self.configuration["gene_sets"]:
                category_name = category["category"]
                for gene_set in category["sets"]:
                    collection_id = gene_set["collection_id"]
                    set_id = gene_set["set_id"]
                    full_gene_set_id = f"{collection_id}_{set_id}"
                    self.gene_sets_categories[full_gene_set_id] = category_name

    @classmethod
    def build_configuration(cls, configuration):
        """
        Perform a transformation on a given configuration.

        The configuration is transformed to an internal version with more
        specific information on order and ranks.
        """
        if configuration is None:
            return {}
        order = configuration.get("order")
        order_keys = []
        for gene_set in configuration["gene_sets"]:
            order_keys.append(gene_set["category"] + "_rank")
        for genomic_score in configuration["genomic_scores"]:
            order_keys.append(genomic_score["category"])
        for dataset_id in configuration["datasets"].keys():
            order_keys.append(dataset_id)
        if order is None:
            configuration["order"] = order_keys
        else:
            total_categories_count = \
                len(configuration["gene_sets"]) + \
                len(configuration["genomic_scores"]) + \
                len(configuration["datasets"])
            assert all(x in order_keys for x in order), "Given GP order " \
                "has invalid entries"
            assert len(order) == total_categories_count, "Given GP order " \
                "is missing items"

        return copy(configuration)

    def get_gp(self, gene_symbol: str) -> GPStatistic | None:
        """
        Query a GP by gene_symbol and return the row as statistic.

        Returns None if gene_symbol is not found within the DB.
        """
        table_glot = self.gp_table_glot
        query = sqlglot.select("*").from_(table_glot)
        query = query.where(
            sqlglot.column(
                "symbol_name",
                table=table_glot.alias_or_name,
            ).ilike(f"%{gene_symbol}%"),
        )
        duckdb_connection = duckdb.connect(f"{self.dbfile}", read_only=True)
        with duckdb_connection.cursor() as cursor:
            row = cursor.execute(
                to_duckdb_transpile(query),
            ).df().replace([np.nan], [None]).to_dict("records")[0]
            if not row:
                return None
            return self.gp_from_table_row_single_view(row)

    # FIXME: Too many locals, refactor?
    def gp_from_table_row(self, row: dict) -> dict:
        # pylint: disable=too-many-locals
        """Build an GPStatistic from internal DB row."""
        config = self.configuration
        result = {}

        result["geneSymbol"] = row["symbol_name"]

        for gs_category in config["genomic_scores"]:
            category_name = gs_category["category"]
            for score in gs_category["scores"]:
                score_name = score["score_name"]
                value = row[f"{category_name}_{score_name}"]
                result[".".join([category_name, score_name])] = \
                    value or None

        for gs_category in config["gene_sets"]:
            category_name = gs_category["category"]
            for gene_set in gs_category["sets"]:
                set_id = gene_set["set_id"]
                collection_id = gene_set["collection_id"]
                full_gs_id = f"{collection_id}_{set_id}"
                result[".".join([f"{category_name}_rank", set_id])] = \
                    "\u2713" if row[full_gs_id] else None

        for dataset_id, filters in config["datasets"].items():
            for person_set in filters["person_sets"]:
                set_name = person_set["set_name"]
                for statistic in filters["statistics"]:
                    statistic_id = statistic["id"]
                    count = row[
                        f"{dataset_id}_{set_name}_{statistic_id}"
                    ]
                    rate = row[
                        f"{dataset_id}_{set_name}_{statistic_id}_rate"
                    ]
                    result[".".join([dataset_id, set_name, statistic_id])] = \
                        f"{count} ({round(rate, 2)})" if count else None

        return result

    # FIXME: Too many locals, refactor?
    def gp_from_table_row_single_view(self, row) -> GPStatistic:
        """Create an GPStatistic from single view row."""
        # pylint: disable=too-many-locals
        config = self.configuration
        gene_symbol = row["symbol_name"]
        genomic_scores: Dict[str, Dict] = {}
        for gs_category in config["genomic_scores"]:
            category_name = gs_category["category"]
            genomic_scores[category_name] = {}
            for score in gs_category["scores"]:
                score_name = score["score_name"]
                full_score_id = f"{category_name}_{score_name}"
                genomic_scores[category_name][score_name] = {
                    "value": row[full_score_id],
                    "format": score["format"],
                }

        gene_sets_categories = config["gene_sets"]
        gene_sets = []
        for gs_category in gene_sets_categories:
            category_name = gs_category["category"]
            for gene_set in gs_category["sets"]:
                set_id = gene_set["set_id"]
                collection_id = gene_set["collection_id"]
                full_gs_id = f"{collection_id}_{set_id}"
                if row[full_gs_id] == 1:
                    gene_sets.append(full_gs_id)

        variant_counts = {}
        for dataset_id, filters in config["datasets"].items():
            current_counts: Dict[str, Dict] = {}
            for person_set in filters["person_sets"]:
                set_name = person_set["set_name"]
                for statistic in filters["statistics"]:
                    statistic_id = statistic["id"]
                    counts = current_counts.get(set_name)
                    if not counts:
                        current_counts[set_name] = {}
                        counts = current_counts[set_name]

                    count = row[
                        f"{dataset_id}_{set_name}_{statistic_id}"
                    ]
                    rate = row[
                        f"{dataset_id}_{set_name}_{statistic_id}_rate"
                    ]
                    counts[statistic_id] = {
                        "count": count,
                        "rate": rate,
                    }
            variant_counts[dataset_id] = current_counts

        return GPStatistic(
            gene_symbol, gene_sets,
            genomic_scores, variant_counts,
        )

    def _transform_sort_by(self, sort_by: str) -> str:
        sort_by_tokens = sort_by.split(".")
        if sort_by.startswith("gene_set_"):
            sort_by = sort_by.replace("gene_set_", "", 1)
        if "_rank" in sort_by_tokens[0]:
            collection_id = ""
            category = sort_by_tokens[0].replace("_rank", "")
            if len(sort_by_tokens) == 2:
                for gs_category in self.configuration["gene_sets"]:
                    if gs_category["category"] != category:
                        continue
                    for gene_set in gs_category["sets"]:
                        if gene_set["set_id"] == sort_by_tokens[1]:
                            collection_id = gene_set["collection_id"]
                sort_by = ".".join((collection_id, sort_by_tokens[1]))
        return sort_by.replace(".", "_")

    def query_gps(
        self,
        page: int,
        symbol_like: str | None = None,
        sort_by: str | None = None,
        order: str | None = None,
    ) -> list:
        """
        Perform paginated query and return list of GPs.

        Parameters:
            page - Which page to fetch.
            symbol_like - Which gene symbol to search for, supports
            incomplete search
            sort_by - Column to sort by
            order - "asc" or "desc"
        """
        table_glot = self.gp_table_glot

        query = sqlglot.select("*").from_(table_glot)
        if symbol_like:
            query = query.where(
                sqlglot.column(
                    "symbol_name",
                    table=table_glot.alias_or_name,
                ).ilike(f"%{symbol_like}%"),
            )

        if sort_by is not None:
            if order is None:
                order = "desc"
            sort_by = self._transform_sort_by(sort_by)
            order = "DESC" if order == "desc" else "ASC"
            query = query.order_by(f'"{sort_by}" {order}')

        if page is not None:
            query = query.limit(self.PAGE_SIZE).offset(
                self.PAGE_SIZE * (page - 1),
            )

        # Can't have multiple connections with sqlite db alive when
        # one of those does a 'write' action. That's why connect here:
        duckdb_connection = duckdb.connect(f"{self.dbfile}", read_only=True)
        with duckdb_connection.cursor() as cursor:
            return cursor.execute(
                to_duckdb_transpile(query),
            ).df().fillna(0).to_dict("records")

    def list_symbols(
        self, page: int, symbol_like: str | None = None,
    ) -> list[str]:
        """
        Perform paginated query and return list of gene symbols.

        Parameters:
            page - Which page to fetch.
            symbol_like - Which gene symbol to search for, supports
            incomplete search
        """
        table_glot = self.gp_table_glot

        query = sqlglot.select(
            sqlglot.column(
                "symbol_name",
                table=table_glot.alias_or_name,
            )
        ).from_(table_glot)
        if symbol_like:
            query = query.where(
                sqlglot.column(
                    "symbol_name",
                    table=table_glot.alias_or_name,
                ).ilike(f"{symbol_like}%"),
            )

        query = query.order_by("symbol_name ASC")

        if page is not None:
            query = query.limit(self.PAGE_SIZE).offset(
                self.PAGE_SIZE * (page - 1),
            )

        duckdb_connection = duckdb.connect(f"{self.dbfile}", read_only=True)
        with duckdb_connection.cursor() as cursor:
            return [
                row["symbol_name"] for row in cursor.execute(
                    to_duckdb_transpile(query),
                ).df().fillna(0).to_dict("records")
            ]

    def drop_gp_table(self):
        with self.engine.begin() as connection:
            connection.execute("DROP TABLE IF EXISTS gene_profile")
            connection.commit()

    def gp_table_exists(self):
        insp = inspect(self.engine)
        with self.engine.begin() as connection:
            has_gp_table = insp.dialect.has_table(
                connection, "gene_profile",
            )
            return has_gp_table

    # FIXME: Too many locals, refactor?
    def _gp_table_columns(self):  # pylint: disable=too-many-locals
        columns = {}
        columns["symbol_name"] = \
            Column("symbol_name", String(64), primary_key=True)
        if len(self.configuration) == 0:
            return columns
        for category in self.configuration["gene_sets"]:
            category_name = category["category"]

            rank_col = f"{category_name}_rank"

            columns[rank_col] = Column(rank_col, Integer())
            for gene_set in category["sets"]:
                set_id = gene_set["set_id"]
                collection_id = gene_set["collection_id"]
                full_set_id = f"{collection_id}_{set_id}"
                columns[full_set_id] = Column(full_set_id, Integer())

        for category in self.configuration["genomic_scores"]:
            category_name = category["category"]
            for score in category["scores"]:
                score_name = score["score_name"]
                col = f"{category_name}_{score_name}"
                columns[col] = Column(col, Float())

        for dataset_id in self.configuration["datasets"].keys():
            config_section = self.configuration["datasets"][dataset_id]
            for person_set in config_section["person_sets"]:
                set_name = person_set["set_name"]
                for stat in config_section["statistics"]:
                    stat_id = stat["id"]
                    column_name = f"{dataset_id}_{set_name}_{stat_id}"
                    columns[column_name] = Column(column_name, Float())
                    rate_col_name = f"{column_name}_rate"
                    columns[rate_col_name] = Column(rate_col_name, Float())
        return columns

    def _create_gp_table(self) -> None:
        columns = self._gp_table_columns().values()

        self.gp_table = Table(
            "gene_profile",
            self.metadata,
            *columns,
        )

        self.gp_table_glot = sqlglot.table("gene_profile")

        self.metadata.create_all(self.engine)

    def _clear_gp_table(self, connection=None):
        query = self.gp_table.delete()
        if connection is not None:
            connection.execute(query)
            return

        with self.engine.begin() as conn:
            conn.execute(query)
            conn.commit()

    def insert_gp(self, gp, connection=None):
        """Insert a GP into the DB."""
        insert_map = self._create_insert_map(gp)
        if connection is not None:
            connection.execute(
                insert(self.gp_table).values(**insert_map),
            )
            return

        with self.engine.begin() as conn:
            conn.execute(
                insert(self.gp_table).values(**insert_map),
            )
            conn.commit()

    # FIXME: Too many locals, refactor?
    def _create_insert_map(self, gp):  # pylint: disable=too-many-locals
        insert_map = {
            "symbol_name": gp.gene_symbol,
        }
        gs_categories_count = {
            c["category"]: 0
            for c in self.configuration["gene_sets"]
        }
        for gsc in self.configuration["gene_sets"]:
            category = gsc["category"]
            for gene_set in gsc["sets"]:
                collection_id = gene_set["collection_id"]
                gs_id = gene_set["set_id"]
                set_col = f"{collection_id}_{gs_id}"
                if set_col in gp.gene_sets:
                    insert_map[set_col] = 1
                    gs_categories_count[category] += 1
                else:
                    insert_map[set_col] = 0

        for category, count in gs_categories_count.items():
            insert_map[f"{category}_rank"] = count

        for category, scores in gp.genomic_scores.items():
            for score_id, score in scores.items():
                insert_map[f"{category}_{score_id}"] = score

        for study_id, ps_counts in gp.variant_counts.items():
            for person_set_id, eff_type_counts in ps_counts.items():
                for eff_type, count in eff_type_counts.items():
                    count_col = f"{study_id}_{person_set_id}_{eff_type}"
                    insert_map[count_col] = 0
                    insert_map[f"{count_col}_rate"] = 0
        return insert_map

    def insert_gps(self, gps):
        """Insert multiple GPStatistics into the DB."""
        with self.engine.begin() as connection:
            self._clear_gp_table(connection)
            gp_count = len(gps)
            for idx, gp in enumerate(gps, 1):
                self.insert_gp(gp, connection)

                if idx % 1000 == 0:
                    logger.info(
                        "Inserted %s/%s GPs into DB", idx, gp_count)
            logger.info("Done!")
            connection.commit()

    def update_gps_with_values(self, gs_values: dict[str, Any]) -> None:
        with self.engine.begin() as connection:
            for gs, values in gs_values.items():
                update = self.gp_table.update().values(**values).where(
                    self.gp_table.c.symbol_name == gs,
                )
                connection.execute(update)
            connection.commit()
