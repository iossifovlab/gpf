import logging
from copy import copy

from dae.autism_gene_profile.statistic import AGPStatistic
from sqlalchemy import MetaData, create_engine, inspect, nullslast
from sqlalchemy import Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.sql import select, insert, join, delete, and_, desc, asc
from sqlalchemy.orm import aliased
from dae.utils.sql_utils import CreateView

logger = logging.getLogger(__name__)


class AutismGeneProfileDB:

    PAGE_SIZE = 100

    def __init__(self, configuration, dbfile, clear=False):
        self.dbfile = dbfile
        self.engine = create_engine("sqlite:///{}".format(dbfile))
        self.metadata = MetaData(self.engine)
        self.configuration = self._build_configuration(configuration)
        self.build_gene_profile_db(clear)
        self._agp_view = None
        if self.cache_table_exists():
            self.cache_table = self._create_db_cache_table(autoload=True)
        self.gene_sets_categories = dict()
        if len(self.configuration.keys()):
            for category in self.configuration["gene_sets"]:
                category_name = category["category"]
                for gene_set in category["sets"]:
                    collection_id = gene_set["collection_id"]
                    set_id = gene_set["set_id"]
                    full_gene_set_id = f"{collection_id}_{set_id}"
                    self.gene_sets_categories[full_gene_set_id] = category_name

    @property
    def agp_view(self):
        if self._agp_view is None:
            self._agp_view = Table("agp_view", self.metadata, autoload=True)
        return self._agp_view

    def _build_configuration(self, configuration):
        if configuration is None:
            return dict()
        return copy(configuration)

    def _get_genomic_scores(self, gene_symbol_id):
        s = select([
            self.genomic_scores.c.score_name,
            self.genomic_scores.c.score_value,
            self.genomic_scores.c.score_category
        ]).where(
            self.genomic_scores.c.symbol_id == gene_symbol_id,
        )
        with self.engine.connect() as connection:
            genomic_scores = connection.execute(s).fetchall()
        return genomic_scores

    def _get_studies(self):
        s = select(self.studies.c)
        with self.engine.connect() as connection:
            studies = connection.execute(s).fetchall()
        return [
            {"id": row[0], "study_id": row[1]}
            for row in studies
        ]

    def _get_study_ids(self, connection=None):
        s = select(self.studies.c)
        if connection is not None:
            studies = connection.execute(s).fetchall()
        else:
            with self.engine.connect() as connection:
                studies = connection.execute(s).fetchall()
        return {row[1]: row[0] for row in studies}

    def _get_variant_counts(self, gene_symbol_id):
        j = join(
            self.variant_counts, self.studies,
            self.variant_counts.c.study_id == self.studies.c.id
        )
        s = select([
            self.studies.c.study_id,
            self.variant_counts.c.people_group,
            self.variant_counts.c.statistic_id,
            self.variant_counts.c.count,
            self.variant_counts.c.rate
        ]).select_from(j).where(
            self.variant_counts.c.symbol_id == gene_symbol_id,
        )
        with self.engine.connect() as connection:
            variant_counts = connection.execute(s).fetchall()
        return variant_counts

    def _get_gene_set(self, gene_set_id):
        s = select([self.gene_sets.c.id, self.gene_sets.c.set_id]).where(
            self.gene_sets.c.set_id == gene_set_id
        )
        with self.engine.connect() as connection:
            gene_sets = connection.execute(s).fetchall()
        if len(gene_sets):
            return gene_sets[0]
        return None

    def _get_gene_sets(self):
        s = select(self.gene_sets.c)
        with self.engine.connect() as connection:
            sets = connection.execute(s).fetchall()
        return sets

    def _get_gene_set_ids(self):
        s = select(self.gene_sets.c)
        with self.engine.connect() as connection:
            sets = connection.execute(s).fetchall()
        return {f"{gs.collection_id}_{gs.set_id}": gs.id for gs in sets}

    def _get_gene_symbol_sets(self, gene_symbol_id):
        j = join(
            self.gene_symbol_sets, self.gene_sets,
            self.gene_symbol_sets.c.set_id == self.gene_sets.c.id
        )
        s = select(
            [
                self.gene_sets.c.set_id,
                self.gene_sets.c.collection_id,
                self.gene_symbol_sets.c.present
            ]
        ).select_from(j).where(
            self.gene_symbol_sets.c.symbol_id == gene_symbol_id,
        )
        with self.engine.connect() as connection:
            gene_sets = connection.execute(s).fetchall()
        return gene_sets

    def _get_gene_symbol_id(self, gene_symbol):
        s = select([self.gene_symbols.c.id]).where(
            self.gene_symbols.c.symbol_name == gene_symbol,
        )
        with self.engine.connect() as connection:
            gene_symbols = connection.execute(s).fetchall()
        return gene_symbols[0].id

    def _get_gene_symbols(self):
        s = select(self.gene_symbols.c)
        with self.engine.connect() as connection:
            gene_symbols = connection.execute(s).fetchall()
        return [gs.symbol_name for gs in gene_symbols]

    def _get_gene_symbol_ids(self):
        s = select(self.gene_symbols.c)
        with self.engine.connect() as connection:
            gene_symbols = connection.execute(s).fetchall()
        return {gs.symbol_name: gs.id for gs in gene_symbols}

    def get_agp(self, gene_symbol):
        symbol_id = self._get_gene_symbol_id(gene_symbol)
        sets_in = list(self._get_gene_symbol_sets(symbol_id))
        sets_in = [
            row[0] for row in
            filter(lambda row: row["present"] == 1, sets_in)
        ]

        db_genomic_scores = self._get_genomic_scores(symbol_id)
        score_categories = self.configuration["genomic_scores"]

        genomic_scores = dict()

        for score in db_genomic_scores:
            score_name = score["score_name"]
            score_value = score["score_value"]
            category = score["score_category"]
            if category not in genomic_scores:
                genomic_scores[category] = dict()

            genomic_scores[category][score_name] = {
                "value": score_value
            }

        for category in score_categories:
            category_name = category["category"]
            for score in category["scores"]:
                score_name = score["score_name"]
                fmt = score["format"]
                genomic_scores[category_name][score_name]["format"] = fmt

        variant_counts_rows = self._get_variant_counts(symbol_id)
        variant_counts = dict()
        for row in variant_counts_rows:
            study_name = row[0]
            person_set = row[1]
            statistic_id = row[2]
            count = row[3]
            rate = row[4]

            if study_name not in variant_counts:
                variant_counts[study_name] = dict()

            if person_set not in variant_counts[study_name]:
                variant_counts[study_name][person_set] = dict()

            variant_counts[study_name][person_set][statistic_id] = {
                "count": count,
                "rate": rate
            }

        return AGPStatistic(
            gene_symbol, sets_in,
            genomic_scores, variant_counts
        )

    def get_all_agps(self):
        symbols = self._get_gene_symbols()
        agps = []
        for symbol in symbols:
            agps.append(self.get_agp(symbol))
        return agps

    def _transform_sort_by(self, sort_by):
        if sort_by.startswith("gene_set_"):
            sort_by = sort_by.replace("gene_set_", "", 1)
        return sort_by

    def query_agps(
            self, page, symbol_like=None, sort_by=None, order=None,
            force_view=False):
        if force_view:
            table = self.agp_view
        elif self.cache_table_exists():
            table = self.cache_table
        else:
            table = self.agp_view

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

    def _build_gene_symbols_table(self):
        self.gene_symbols = Table(
            "gene_symbols",
            self.metadata,
            Column("id", Integer(), primary_key=True),
            Column(
                "symbol_name",
                String(64),
                nullable=False,
                unique=True,
                index=True,
            ),
        )

    def _build_gene_sets_table(self):
        self.gene_sets = Table(
            "gene_sets",
            self.metadata,
            Column("id", Integer(), primary_key=True),
            Column(
                "set_id",
                String(64),
                nullable=False,
                unique=True,
                index=True,
            ),
            Column("collection_id", String(64), nullable=False)
        )

    def _build_gene_symbol_sets_table(self):
        self.gene_symbol_sets = Table(
            "gene_symbol_sets",
            self.metadata,
            Column("id", Integer(), primary_key=True),
            Column("symbol_id", ForeignKey("gene_symbols.id")),
            Column("set_id", ForeignKey("gene_sets.id")),
            Column("present", Integer())
        )

    def _populate_gene_sets_table(self, sets):
        with self.engine.connect() as connection:
            connection.execute(
                insert(self.gene_sets).values(
                    [
                        {
                            'set_id': s["set_id"],
                            'collection_id': s["collection_id"]
                        }
                        for s in sets
                    ]
                )
            )

    def _populate_studies_table(self, studies):
        with self.engine.connect() as connection:
            connection.execute(
                insert(self.studies).values(
                    [{'study_id': s} for s in studies]
                )
            )

    def _build_genomic_scores_table(self):
        self.genomic_scores = Table(
            "genomic_scores",
            self.metadata,
            Column("id", Integer(), primary_key=True),
            Column("symbol_id", ForeignKey("gene_symbols.id")),
            Column("score_name", String(64), nullable=False),
            Column("score_value", Float()),
            Column("score_category", String(64))
        )

    def _build_variant_counts_table(self):
        self.variant_counts = Table(
            "variant_counts",
            self.metadata,
            Column("id", Integer(), primary_key=True),
            Column("symbol_id", ForeignKey("gene_symbols.id")),
            Column("study_id", ForeignKey("studies.study_id")),
            Column("people_group", String(64), nullable=False),
            Column("statistic_id", String(64), nullable=False),
            Column("count", Integer()),
            Column("rate", Float())
        )

    def _build_studies_table(self):
        self.studies = Table(
            "studies",
            self.metadata,
            Column("id", Integer(), primary_key=True),
            Column(
                "study_id",
                String(64),
                nullable=False,
                unique=True,
                index=True,
            ),
        )

    def _build_categories_ranks_table(self):
        self.categories_ranks = Table(
            "categories_ranks",
            self.metadata,
            Column(
                "symbol_id",
                ForeignKey("gene_symbols.id"),
                primary_key=True
            ),
            Column("category_id", String(32), primary_key=True),
            Column("count", Integer())
        )

    def drop_cache_table(self):
        with self.engine.connect() as connection:
            connection.execute("DROP TABLE IF EXISTS agp_view_cache")

    def cache_table_exists(self):
        insp = inspect(self.engine)
        with self.engine.connect() as connection:
            has_cache_table = insp.dialect.has_table(
                connection, "agp_view_cache"
            )
            return has_cache_table

    def _cache_table_columns(self):
        columns = {}
        columns["symbol_name"] = \
            Column("symbol_name", String(64), primary_key=True)
        for category in self.configuration["gene_sets"]:
            category_name = category["category"]

            rank_col = f"{category_name}_rank"

            columns[rank_col] = Column(rank_col, String(32))
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

    def _create_db_cache_table(self, autoload=False):
        columns = self._cache_table_columns().values()

        return Table(
            "agp_view_cache",
            self.metadata,
            *columns,
            autoload=autoload
        )

    def _clear_cache_table(self):
        d = self.cache_table.delete()
        with self.engine.connect() as connection:
            connection.execute(d)

    def generate_cache_table(self):
        self.drop_cache_table()
        self.cache_table = self._create_db_cache_table()
        self.metadata.create_all(tables=[self.cache_table])
        columns = list(self._cache_table_columns().keys())
        s = self.agp_view.select()
        ins = self.cache_table.insert().from_select(columns, s)
        with self.engine.connect() as connection:
            connection.execute(ins)

    def build_agp_view(self):
        study_ids = self._get_study_ids()
        gene_set_ids = self._get_gene_set_ids()
        current_join = None
        select_cols = [self.gene_symbols.c.symbol_name]

        for category in self.configuration["gene_sets"]:
            category_id = category["category"]
            table_alias = aliased(
                self.categories_ranks,
                f"{category_id}_rank"
            )
            left = current_join
            if left is None:
                left = self.gene_symbols

            current_join = join(
                left, table_alias,
                and_(
                    self.gene_symbols.c.id == table_alias.c.symbol_id,
                    table_alias.c.category_id == category_id
                )
            )

            select_cols.append(
                table_alias.c.count.label(f"{category_id}_rank")
            )

            for gs in category["sets"]:
                set_id = gs["set_id"]
                collection_id = gs["collection_id"]
                full_set_id = f"{collection_id}_{set_id}"
                set_alias = full_set_id
                table_alias = aliased(
                    self.gene_symbol_sets,
                    set_alias
                )
                left = current_join
                if left is None:
                    left = self.gene_symbols

                current_join = join(
                    left, table_alias,
                    and_(
                        self.gene_symbols.c.id == table_alias.c.symbol_id,
                        table_alias.c.set_id == gene_set_ids[full_set_id]
                    ),
                    isouter=True
                )

                select_cols.append(table_alias.c.present.label(set_alias))

        for category in self.configuration["genomic_scores"]:
            category_name = category["category"]
            for score in category["scores"]:
                score_name = score["score_name"]
                score_alias = f"{category_name}_{score_name}"
                table_alias = aliased(
                    self.genomic_scores,
                    score_alias
                )
                left = current_join
                if left is None:
                    left = self.gene_symbols

                current_join = join(
                    left, table_alias,
                    and_(
                        self.gene_symbols.c.id == table_alias.c.symbol_id,
                        table_alias.c.score_category == category_name,
                        table_alias.c.score_name == score_name
                    )
                )

                select_cols.append(
                    table_alias.c.score_value.label(score_alias)
                )

        for dataset_id, dataset in self.configuration["datasets"].items():
            config_section = self.configuration["datasets"][dataset_id]
            db_study_id = study_ids[dataset_id]
            for person_set in config_section["person_sets"]:
                set_name = person_set["set_name"]
                for stat in config_section["statistics"]:
                    stat_id = stat["id"]
                    count_alias = f"{dataset_id}_{set_name}_{stat_id}"
                    rate_alias = f"{count_alias}_rate"
                    table_alias = aliased(
                        self.variant_counts,
                        count_alias
                    )
                    left = current_join
                    if left is None:
                        left = self.gene_symbols

                    current_join = join(
                        left, table_alias,
                        and_(
                            self.gene_symbols.c.id == table_alias.c.symbol_id,
                            table_alias.c.study_id == db_study_id,
                            table_alias.c.people_group == set_name,
                            table_alias.c.statistic_id == stat_id
                        )
                    )
                    select_cols.extend([
                        table_alias.c.count.label(count_alias),
                        table_alias.c.rate.label(rate_alias)
                    ])

        view_query = select(select_cols).select_from(current_join)

        with self.engine.connect() as connection:
            connection.execute("DROP VIEW IF EXISTS agp_view")
            view_create = CreateView("agp_view", view_query)
            connection.execute(view_create)

        self._agp_view = Table("agp_view", self.metadata, autoload=True)

    def build_gene_profile_db(self, clear=False):
        self._build_gene_symbols_table()
        self._build_gene_sets_table()
        self._build_gene_symbol_sets_table()
        self._build_studies_table()
        self._build_genomic_scores_table()
        self._build_variant_counts_table()
        self._build_categories_ranks_table()
        if clear:
            self.metadata.drop_all()
        self.metadata.create_all()

    def clear_all_tables(self):
        with self.engine.connect() as connection:
            connection.execute(delete(self.variant_counts))
            connection.execute(delete(self.gene_symbol_sets))
            connection.execute(delete(self.genomic_scores))
            connection.execute(delete(self.studies))
            connection.execute(delete(self.gene_symbols))
            connection.execute(delete(self.gene_sets))

    def populate_data_tables(self, studies):
        gene_sets_config = self.configuration["gene_sets"]
        gene_sets = []
        for category in gene_sets_config:
            for gene_set in category["sets"]:
                gene_sets.append(gene_set)
        self._populate_gene_sets_table(gene_sets)
        self._populate_studies_table(studies)

    def insert_agp(self, agp):
        with self.engine.connect() as connection:
            connection.execute(
                insert(self.gene_symbols).values(symbol_name=agp.gene_symbol)
            )
            symbol_id = self._get_gene_symbol_id(agp.gene_symbol)
            for category, scores in agp.genomic_scores.items():
                for name, value in scores.items():
                    connection.execute(
                        insert(self.genomic_scores).values(
                            symbol_id=symbol_id,
                            score_name=name,
                            score_value=value,
                            score_category=category
                        )
                    )
            gene_sets = self._get_gene_sets()
            gs_categories_count = {
                c["category"]: 0 for c in self.configuration["gene_sets"]
            }
            for gs_row in gene_sets:
                set_id = gs_row["set_id"]
                collection_id = gs_row["collection_id"]
                full_set_id = f"{collection_id}_{set_id}"
                if full_set_id in agp.gene_sets:
                    present = 1
                else:
                    present = 0
                db_set_id = gs_row["id"]
                connection.execute(
                    insert(self.gene_symbol_sets).values(
                        symbol_id=symbol_id,
                        set_id=db_set_id,
                        present=present
                    )
                )

                if present == 1:
                    category = self.gene_sets_categories[full_set_id]
                    gs_categories_count[category] += 1

            for category, count in gs_categories_count.items():
                connection.execute(
                    insert(self.categories_ranks).values(
                        symbol_id=symbol_id,
                        category_id=category,
                        count=count
                    )
                )

            study_ids = self._get_study_ids()
            for study, counts in agp.variant_counts.items():
                study_id = study_ids[study]
                for people_group, statistics in counts.items():
                    for statistic_id, stat in statistics.items():
                        count = stat["count"]
                        rate = stat["rate"]
                        connection.execute(
                            insert(self.variant_counts).values(
                                symbol_id=symbol_id,
                                study_id=study_id,
                                people_group=people_group,
                                statistic_id=statistic_id,
                                count=count,
                                rate=rate
                            )
                        )

    def insert_agps(self, agps):
        study_ids = self._get_study_ids()
        gene_set_ids = self._get_gene_set_ids()
        with self.engine.connect() as connection:
            with connection.begin():
                agp_count = len(agps)
                for idx, agp in enumerate(agps, 1):
                    result = connection.execute(
                        insert(self.gene_symbols).values(
                            symbol_name=agp.gene_symbol
                        )
                    )
                    symbol_id = result.inserted_primary_key[0]

                    for category, scores in agp.genomic_scores.items():
                        for name, value in scores.items():
                            connection.execute(
                                insert(self.genomic_scores).values(
                                    symbol_id=symbol_id,
                                    score_name=name,
                                    score_value=value,
                                    score_category=category
                                )
                            )

                    gs_categories_count = {
                        c["category"]: 0
                        for c in self.configuration["gene_sets"]
                    }
                    for gene_set, set_id in gene_set_ids.items():
                        present = 0
                        if gene_set in agp.gene_sets:
                            present = 1
                        connection.execute(
                            insert(self.gene_symbol_sets).values(
                                symbol_id=symbol_id,
                                set_id=set_id,
                                present=present
                            )
                        )
                        if present == 1:
                            category = self.gene_sets_categories[gene_set]
                            gs_categories_count[category] += 1

                    for category, count in gs_categories_count.items():
                        connection.execute(
                            insert(self.categories_ranks).values(
                                symbol_id=symbol_id,
                                category_id=category,
                                count=count
                            )
                        )

                    for study, counts in agp.variant_counts.items():
                        study_id = study_ids[study]
                        for people_group, statistics in counts.items():
                            for statistic_id, stat in statistics.items():
                                count = stat["count"]
                                rate = stat["rate"]
                                connection.execute(
                                    insert(self.variant_counts).values(
                                        symbol_id=symbol_id,
                                        study_id=study_id,
                                        people_group=people_group,
                                        statistic_id=statistic_id,
                                        count=count,
                                        rate=rate
                                    )
                                )

                    if idx % 1000 == 0:
                        logger.info(f"Inserted {idx}/{agp_count} AGPs into DB")
                logger.info("Done!")
