import logging
from copy import copy

from dae.autism_gene_profile.statistic import AGPStatistic
from sqlalchemy import MetaData, create_engine, inspect, nullslast
from sqlalchemy import Table, Column, Integer, String, Float
from sqlalchemy.sql import insert, desc, asc

logger = logging.getLogger(__name__)


class AutismGeneProfileDB:

    PAGE_SIZE = 40

    def __init__(self, configuration, dbfile, clear=False):
        self.dbfile = dbfile
        self.engine = create_engine("sqlite:///{}".format(dbfile))
        self.metadata = MetaData(self.engine)
        self.configuration = self._build_configuration(configuration)
        self._create_agp_table()
        self.gene_sets_categories = dict()
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

    def _build_configuration(self, configuration):
        if configuration is None:
            return dict()

        order = configuration.get("order")
        if order is None:
            order = []
            for gene_set in configuration["gene_sets"]:
                order.append(gene_set["category"])
            for genomic_score in configuration["genomic_scores"]:
                order.append(genomic_score["category"])
            for dataset_id in configuration["datasets"].keys():
                order.append(dataset_id)
            configuration["order"] = order
        else:
            total_categories_count = \
                len(configuration["gene_sets"]) + \
                len(configuration["genomic_scores"]) + \
                len(configuration["datasets"])
            assert len(order) == total_categories_count, "Given AGP order " \
                "is missing items"

        return copy(configuration)

    def get_agp(self, gene_symbol):
        table = self.agp_table
        s = table.select()
        s = s.where(table.c.symbol_name == gene_symbol)
        with self.engine.connect() as connection:
            row = connection.execute(s).fetchone()
            return self.agp_from_table_row(row)

    def agp_from_table_row(self, row) -> dict:
        config = self.configuration
        result = dict()

        result["geneSymbol"] = row["symbol_name"]

        for gs_category in config["genomic_scores"]:
            category_name = gs_category["category"]
            for score in gs_category["scores"]:
                score_name = score["score_name"]
                value = row[f"{category_name}_{score_name}"]
                result['+'.join([category_name, score_name])] = \
                    value if value is not None else "-"

        for gs_category in config["gene_sets"]:
            category_name = gs_category["category"]
            for gene_set in gs_category["sets"]:
                set_id = gene_set["set_id"]
                collection_id = gene_set["collection_id"]
                full_gs_id = f"{collection_id}_{set_id}"
                result['+'.join([category_name, set_id])] = \
                    bool(row[full_gs_id])
        
        for dataset_id, filters in config["datasets"].items():
            for ps in filters["person_sets"]:
                person_set = ps["set_name"]
                for statistic in filters["statistics"]:
                    statistic_id = statistic["id"]
                    count = row[
                        f"{dataset_id}_{person_set}_{statistic_id}"
                    ]
                    rate = row[
                        f"{dataset_id}_{person_set}_{statistic_id}_rate"
                    ]
                    result['+'.join(["datasets", dataset_id, person_set, statistic_id])] = \
                        f"{count} ({round(rate, 2)})"

        return result

    def _transform_sort_by(self, sort_by):
        if sort_by.startswith("gene_set_"):
            sort_by = sort_by.replace("gene_set_", "", 1)
        return sort_by

    def query_agps(self, page, symbol_like=None, sort_by=None, order=None):
        table = self.agp_table

        s = table.select()
        if symbol_like:
            s = s.where(table.c.symbol_name.like(f"%{symbol_like}%"))

        if sort_by is not None:
            if order is None:
                order = "desc"
            sort_by = self._transform_sort_by(sort_by)
            query_order_func = desc if order == "desc" else asc
            s = s.order_by(nullslast(query_order_func(sort_by)))

        if page is not None:
            s = s.limit(self.PAGE_SIZE).offset(self.PAGE_SIZE*(page-1))
        with self.engine.connect() as connection:
            return connection.execute(s).fetchall()

    def drop_agp_table(self):
        with self.engine.connect() as connection:
            connection.execute("DROP TABLE IF EXISTS autism_gene_profile")

    def agp_table_exists(self):
        insp = inspect(self.engine)
        with self.engine.connect() as connection:
            has_agp_table = insp.dialect.has_table(
                connection, "autism_gene_profile"
            )
            return has_agp_table

    def _agp_table_columns(self):
        columns = {}
        columns["symbol_name"] = \
            Column("symbol_name", String(64), primary_key=True)
        if len(self.configuration) == 0:
            return columns
        for category in self.configuration["gene_sets"]:
            category_name = category["category"]

            rank_col = f"{category_name}_rank"

            columns[rank_col] = Column(rank_col, Integer())
            for gs in category["sets"]:
                set_id = gs["set_id"]
                collection_id = gs["collection_id"]
                full_set_id = f"{collection_id}_{set_id}"
                columns[full_set_id] = Column(full_set_id, Integer())

        for category in self.configuration["genomic_scores"]:
            category_name = category["category"]
            for score in category["scores"]:
                score_name = score["score_name"]
                col = f"{category_name}_{score_name}"
                columns[col] = Column(col, Float())

        for dataset_id, dataset in self.configuration["datasets"].items():
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

        self.metadata.create_all()

    def _clear_agp_table(self, connection=None):
        d = self.agp_table.delete()
        if connection is not None:
            connection.execute(d)
            return

        with self.engine.connect() as connection:
            connection.execute(d)

    def insert_agp(self, agp, connection=None):
        insert_map = self._create_insert_map(agp)
        if connection is None:
            with self.engine.connect() as connection:
                connection.execute(
                    insert(self.agp_table).values(**insert_map)
                )
        else:
            connection.execute(
                insert(self.agp_table).values(**insert_map)
            )

    def _create_insert_map(self, agp):
        insert_map = {
            "symbol_name": agp.gene_symbol,
        }
        gs_categories_count = {
            c["category"]: 0
            for c in self.configuration["gene_sets"]
        }
        for gsc in self.configuration["gene_sets"]:
            category = gsc["category"]
            for gs in gsc["sets"]:
                collection_id = gs["collection_id"]
                gs_id = gs["set_id"]
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
        with self.engine.connect() as connection:
            with connection.begin():
                self._clear_agp_table(connection)
                agp_count = len(agps)
                for idx, agp in enumerate(agps, 1):
                    self.insert_agp(agp, connection)

                    if idx % 1000 == 0:
                        logger.info(f"Inserted {idx}/{agp_count} AGPs into DB")
                logger.info("Done!")
