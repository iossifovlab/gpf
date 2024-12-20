import logging
from copy import copy
from typing import Any

import duckdb
import numpy as np
from box import Box
from sqlglot import column, select, table
from sqlglot.expressions import (
    ColumnConstraint,
    ColumnDef,
    Create,
    DataType,
    PrimaryKeyColumnConstraint,
    Schema,
    delete,
    insert,
    update,
    values,
)

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
        configuration: Box | dict | None,
        dbfile: str,
    ):
        self.dbfile = dbfile
        self.configuration = \
            GeneProfileDBWriter.build_configuration(configuration)
        self.table = table("gene_profile")
        self.gene_sets_categories = {}
        if len(self.configuration.keys()):
            for category in self.configuration["gene_sets"]:
                category_name = category["category"]
                for gene_set in category["sets"]:
                    collection_id = gene_set["collection_id"]
                    set_id = gene_set["set_id"]
                    full_gene_set_id = f"{collection_id}_{set_id}"
                    self.gene_sets_categories[full_gene_set_id] = category_name


    def get_gp(self, gene_symbol: str) -> GPStatistic | None:
        """
        Query a GP by gene_symbol and return the row as statistic.

        Returns None if gene_symbol is not found within the DB.
        """
        query = select("*").from_(self.table)
        query = query.where(
            column(
                "symbol_name",
                table=self.table.alias_or_name,
            ).ilike(f"%{gene_symbol}%"),
        )
        query = query.limit(self.PAGE_SIZE)
        with duckdb.connect(f"{self.dbfile}", read_only=True) as connection:
            rows = connection.execute(
                to_duckdb_transpile(query),
            ).df().replace([np.nan], [None]).to_dict("records")
            if len(rows) == 0:
                return None
            return self.gp_from_table_row_single_view(rows[0])

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
    def gp_from_table_row_single_view(self, row: dict) -> GPStatistic:
        """Create an GPStatistic from single view row."""
        # pylint: disable=too-many-locals
        config = self.configuration
        gene_symbol = row["symbol_name"]
        genomic_scores: dict[str, dict] = {}
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
            current_counts: dict[str, dict] = {}
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
        query = select("*").from_(self.table)
        if symbol_like:
            query = query.where(
                column(
                    "symbol_name",
                    table=self.table.alias_or_name,
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
        with duckdb.connect(f"{self.dbfile}", read_only=True) as connection:
            return connection.execute(
                to_duckdb_transpile(query),
            ).df().replace([np.nan], [None]).to_dict("records")

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
        query = select(
            column(
                "symbol_name",
                table=self.table.alias_or_name,
            ),
        ).from_(self.table)
        if symbol_like:
            query = query.where(
                column(
                    "symbol_name",
                    table=self.table.alias_or_name,
                ).ilike(f"{symbol_like}%"),
            )

        query = query.order_by("symbol_name ASC")

        if page is not None:
            query = query.limit(self.PAGE_SIZE).offset(
                self.PAGE_SIZE * (page - 1),
            )

        with duckdb.connect(f"{self.dbfile}", read_only=True) as connection:
            return [
                row["symbol_name"] for row in connection.execute(
                    to_duckdb_transpile(query),
                ).df().replace([np.nan], [None]).to_dict("records")
            ]


class GeneProfileDBWriter:
    """
    Class for managing the gene profile database.

    Uses SQLite for DB management and supports loading
    and storing to filesystem.
    Has to be supplied a configuration and a path to which to read/write
    the SQLite DB.
    """

    def __init__(
        self,
        configuration: Box | dict | None,
        dbfile: str,
    ):
        self.dbfile = dbfile
        self.configuration = \
            GeneProfileDBWriter.build_configuration(configuration)
        self._create_gp_table()
        self.gene_sets_categories = {}
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
    def build_configuration(cls, configuration: Box | dict | None) -> dict:
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

    def drop_gp_table(self) -> None:
        with duckdb.connect(f"{self.dbfile}") as connection:
            connection.execute("DROP TABLE IF EXISTS gene_profile")
            connection.commit()

    def gp_table_exists(self) -> bool:
        """Checks if gp table exists"""
        duckdb_tables = "duckdb_tables"
        query = select(
            column(
                "table_name",
                table=duckdb_tables,
            ),
        ).from_(duckdb_tables).where(
            column(
                "table_name",
                table=duckdb_tables,
            ).like("gene_profile"),
        ).limit(1)
        with duckdb.connect(f"{self.dbfile}", read_only=True) as connection:
            rows = connection.execute(
                to_duckdb_transpile(query),
            ).df().to_dict("records")

            return len(rows) == 1

    # FIXME: Too many locals, refactor?
    def _gp_table_columns(
        self, *,
        with_types: bool = True,
    ) -> list[ColumnDef]:  # pylint: disable=too-many-locals
        columns = []
        constraints = [ColumnConstraint(kind=PrimaryKeyColumnConstraint())] \
            if with_types else []
        columns.append(
            ColumnDef(
                this="symbol_name",
                kind=DataType(
                    this=DataType.Type.VARCHAR,
                ) if with_types else None,
                constraints=constraints,
            ),
        )
        if len(self.configuration) == 0:
            return columns
        for category in self.configuration["gene_sets"]:
            category_name = category["category"]

            rank_col = f"{category_name}_rank"

            columns.append(
                ColumnDef(
                    this=f'"{rank_col}"',
                    kind=DataType(
                        this=DataType.Type.INT,
                    ) if with_types else None,
                ),
            )
            for gene_set in category["sets"]:
                set_id = gene_set["set_id"]
                collection_id = gene_set["collection_id"]
                full_set_id = f"{collection_id}_{set_id}"
                columns.append(
                    ColumnDef(
                        this=f'"{full_set_id}"',
                        kind=DataType(
                            this=DataType.Type.INT,
                        ) if with_types else None,
                    ),
                )

        for category in self.configuration["genomic_scores"]:
            category_name = category["category"]
            for score in category["scores"]:
                score_name = score["score_name"]
                col = f"{category_name}_{score_name}"
                columns.append(
                    ColumnDef(
                        this=f'"{col}"',
                        kind=DataType(
                            this=DataType.Type.FLOAT,
                        ) if with_types else None,
                    ),
                )

        for dataset_id in self.configuration["datasets"]:
            config_section = self.configuration["datasets"][dataset_id]
            for person_set in config_section["person_sets"]:
                set_name = person_set["set_name"]
                for stat in config_section["statistics"]:
                    stat_id = stat["id"]
                    column_name = f"{dataset_id}_{set_name}_{stat_id}"
                    columns.append(
                        ColumnDef(
                            this=f'"{column_name}"',
                            kind=DataType(
                                this=DataType.Type.FLOAT,
                            ) if with_types else None,
                        ),
                    )
                    rate_col_name = f"{column_name}_rate"
                    columns.append(
                        ColumnDef(
                            this=f'"{rate_col_name}"',
                            kind=DataType(
                                this=DataType.Type.FLOAT,
                            ) if with_types else None,
                        ),
                    )
        return columns

    def _create_gp_table(self) -> None:
        self.table = table("gene_profile")
        self.schema = Schema(
            this=self.table,
            expressions=self._gp_table_columns(),
        )

        query = Create(this=self.schema, kind="TABLE", exists=True)
        with duckdb.connect(f"{self.dbfile}") as connection:
            connection.execute(to_duckdb_transpile(query))

    def _clear_gp_table(
        self,
        connection: duckdb.DuckDBPyConnection | None = None,
    ) -> None:
        query = delete(self.table)
        if connection is not None:
            connection.execute(to_duckdb_transpile(query))
            return

        with duckdb.connect(f"{self.dbfile}") as connection:
            connection.execute(to_duckdb_transpile(query))

    def insert_gp(
        self,
        gp: GPStatistic,
        connection: duckdb.DuckDBPyConnection | None = None,
    ) -> None:
        """Insert a GP into the DB."""
        insert_map = self._create_insert_map(gp)
        query = insert(
            values([tuple(insert_map.values())]),
            self.table,
            columns=list(insert_map.keys()),
        )
        if connection is not None:
            connection.execute(to_duckdb_transpile(query))
            return

        with duckdb.connect(f"{self.dbfile}") as connection:
            connection.execute(to_duckdb_transpile(query))

    # FIXME: Too many locals, refactor?
    def _create_insert_map(
        self,
        gp: GPStatistic,
    ) -> dict:  # pylint: disable=too-many-locals
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

        insert_map.update(dict(gp.variant_counts.items()))

        return insert_map

    def insert_gps(
        self,
        gps: dict,
    ) -> None:
        """Insert multiple GPStatistics into the DB."""
        with duckdb.connect(f"{self.dbfile}") as connection:
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
        """Update gp statistic with values"""
        with duckdb.connect(f"{self.dbfile}") as connection:
            for gs, vals in gs_values.items():
                query = update(
                    self.table,
                    vals,
                    where=column(
                        "symbol_name",
                        table=self.table.alias_or_name,
                    ).eq(gs),
                )
                connection.execute(to_duckdb_transpile(query))
            connection.commit()
