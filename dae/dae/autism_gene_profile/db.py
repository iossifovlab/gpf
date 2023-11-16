import logging
from typing import Optional, Dict
from copy import copy

from sqlalchemy import create_engine, inspect, nullslast  # type: ignore
from sqlalchemy import MetaData, Table, Column, Integer, String, Float
from sqlalchemy.sql import insert, desc, asc
from dae.autism_gene_profile.statistic import AGPStatistic

logger = logging.getLogger(__name__)


class AutismGeneProfileDB:
    """
    Class for managing the autism gene profile database.

    Uses SQLite for DB management and supports loading
    and storing to filesystem.
    Has to be supplied a configuration and a path to which to read/write
    the SQLite DB.
    """

    PAGE_SIZE = 20

    def __init__(self, configuration, dbfile, clear=False):
        self.dbfile = dbfile
        self.engine = create_engine(f"sqlite:///{dbfile}")
        self.metadata = MetaData()
        self.configuration = \
            AutismGeneProfileDB.build_configuration(configuration)
        self._create_agp_table()
        self.gene_sets_categories = {}
        if clear:
            self._clear_agp_table()
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
            assert all(x in order_keys for x in order), "Given AGP order " \
                "has invalid entries"
            assert len(order) == total_categories_count, "Given AGP order " \
                "is missing items"

        return copy(configuration)

    def get_agp(self, gene_symbol) -> Optional[AGPStatistic]:
        """
        Query an AGP by gene_symbol and return the row as statistic.

        Returns None if gene_symbol is not found within the DB.
        """
        table = self.agp_table
        query = table.select()
        query = query.where(table.c.symbol_name == gene_symbol)
        with self.engine.begin() as connection:
            row = connection.execute(query).fetchone()
            if not row:
                return None
            return self.agp_from_table_row_single_view(row)

    # FIXME: Too many locals, refactor?
    def agp_from_table_row(self, row) -> dict:
        # pylint: disable=too-many-locals
        """Build an AGPStatistic from internal DB row."""
        config = self.configuration
        row = row._mapping  # pylint: disable=protected-access
        result = {}

        result["geneSymbol"] = row["symbol_name"]

        for gs_category in config["genomic_scores"]:
            category_name = gs_category["category"]
            for score in gs_category["scores"]:
                score_name = score["score_name"]
                value = row[f"{category_name}_{score_name}"]
                result[".".join([category_name, score_name])] = value

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
    def agp_from_table_row_single_view(self, row) -> AGPStatistic:
        """Create an AGPStatistic from single view row."""
        # pylint: disable=too-many-locals
        config = self.configuration
        row = row._mapping  # pylint: disable=protected-access
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
                    "format": score["format"]
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
                        "rate": rate
                    }
            variant_counts[dataset_id] = current_counts

        return AGPStatistic(
            gene_symbol, gene_sets,
            genomic_scores, variant_counts
        )

    def _transform_sort_by(self, sort_by):
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

    def query_agps(self, page, symbol_like=None, sort_by=None, order=None):
        """
        Perform paginated query and return list of AGPs.

        Parameters:
            page - Which page to fetch.
            symbol_like - Which gene symbol to search for, supports
            incomplete search
            sort_by - Column to sort by
            order - "asc" or "desc"
        """
        table = self.agp_table

        query = table.select()
        if symbol_like:
            query = query.where(table.c.symbol_name.like(f"%{symbol_like}%"))

        if sort_by is not None:
            if order is None:
                order = "desc"
            sort_by = self._transform_sort_by(sort_by)
            query_order_func = desc if order == "desc" else asc
            query = query.order_by(nullslast(query_order_func(sort_by)))

        if page is not None:
            query = query.limit(self.PAGE_SIZE).offset(
                self.PAGE_SIZE * (page - 1)
            )
        with self.engine.begin() as connection:
            return connection.execute(query).fetchall()

    def drop_agp_table(self):
        with self.engine.begin() as connection:
            connection.execute("DROP TABLE IF EXISTS autism_gene_profile")
            connection.commit()

    def agp_table_exists(self):
        insp = inspect(self.engine)
        with self.engine.begin() as connection:
            has_agp_table = insp.dialect.has_table(
                connection, "autism_gene_profile"
            )
            return has_agp_table

    # FIXME: Too many locals, refactor?
    def _agp_table_columns(self):  # pylint: disable=too-many-locals
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

    def _create_agp_table(self):
        columns = self._agp_table_columns().values()

        self.agp_table = Table(
            "autism_gene_profile",
            self.metadata,
            *columns,
        )

        self.metadata.create_all(self.engine)

    def _clear_agp_table(self, connection=None):
        query = self.agp_table.delete()
        if connection is not None:
            connection.execute(query)
            return

        with self.engine.begin() as conn:
            conn.execute(query)
            conn.commit()

    def insert_agp(self, agp, connection=None):
        """Insert an AGP into the DB."""
        insert_map = self._create_insert_map(agp)
        if connection is not None:
            connection.execute(
                insert(self.agp_table).values(**insert_map)
            )
            return

        with self.engine.begin() as conn:
            conn.execute(
                insert(self.agp_table).values(**insert_map)
            )
            conn.commit()

    # FIXME: Too many locals, refactor?
    def _create_insert_map(self, agp):  # pylint: disable=too-many-locals
        insert_map = {
            "symbol_name": agp.gene_symbol,
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
                if set_col in agp.gene_sets:
                    insert_map[set_col] = 1
                    gs_categories_count[category] += 1
                else:
                    insert_map[set_col] = 0

        for category, count in gs_categories_count.items():
            insert_map[f"{category}_rank"] = count

        for category, scores in agp.genomic_scores.items():
            for score_id, score in scores.items():
                insert_map[f"{category}_{score_id}"] = score

        for study_id, ps_counts in agp.variant_counts.items():
            for person_set_id, eff_type_counts in ps_counts.items():
                for eff_type, count in eff_type_counts.items():
                    count_col = f"{study_id}_{person_set_id}_{eff_type}"
                    insert_map[count_col] = count["count"]
                    insert_map[f"{count_col}_rate"] = count["rate"]
        return insert_map

    def insert_agps(self, agps):
        """Insert multiple AGPStatistics into the DB."""
        with self.engine.begin() as connection:
            self._clear_agp_table(connection)
            agp_count = len(agps)
            for idx, agp in enumerate(agps, 1):
                self.insert_agp(agp, connection)

                if idx % 1000 == 0:
                    logger.info(
                        "Inserted %s/%s AGPs into DB", idx, agp_count)
            logger.info("Done!")
            connection.commit()
