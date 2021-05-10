import logging
from copy import copy

from dae.autism_gene_profile.statistic import AGPStatistic
from sqlalchemy import MetaData, create_engine, inspect
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
        if self.cache_table_exists() and False:
            self.cache_table = self._create_db_cache_table(autoload=True)

    @property
    def agp_view(self):
        if self._agp_view is None:
            self._agp_view = Table("agp_view", self.metadata, autoload=True)
        return self._agp_view

    def _build_configuration(self, configuration):
        if configuration is None:
            return dict()
        configuration = copy(configuration)

        for dataset in configuration["datasets"]:
            dataset_dict = configuration["datasets"][dataset]
            person_sets = dataset_dict["person_sets"]
            dataset_dict["person_sets"] = [
                ps["set_name"] for ps in person_sets
            ]
        return configuration

    def _get_autism_scores(self, gene_symbol_id):
        s = select([
            self.autism_scores.c.score_name,
            self.autism_scores.c.score_value,
        ]).where(
            self.autism_scores.c.symbol_id == gene_symbol_id,
        )
        with self.engine.connect() as connection:
            autism_scores = connection.execute(s).fetchall()
        return autism_scores

    def _get_protection_scores(self, gene_symbol_id):
        s = select([
            self.protection_scores.c.score_name,
            self.protection_scores.c.score_value,
        ]).where(
            self.protection_scores.c.symbol_id == gene_symbol_id,
        )
        with self.engine.connect() as connection:
            protection_scores = connection.execute(s).fetchall()
        return protection_scores

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
            self.variant_counts.c.effect_type,
            self.variant_counts.c.count
        ]).select_from(j).where(
            self.variant_counts.c.symbol_id == gene_symbol_id,
        )
        with self.engine.connect() as connection:
            variant_counts = connection.execute(s).fetchall()
        return variant_counts

    def _get_gene_set(self, gene_set_name):
        s = select([self.gene_sets.c.id, self.gene_sets.c.set_name]).where(
            self.gene_sets.c.set_name == gene_set_name
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
        return {gs.set_name: gs.id for gs in sets}

    def _get_gene_symbol_sets(self, gene_symbol_id):
        j = join(
            self.gene_symbol_sets, self.gene_sets,
            self.gene_symbol_sets.c.set_id == self.gene_sets.c.id
        )
        s = select(
            [
                self.gene_sets.c.set_name,
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
        protection_scores = self._get_protection_scores(symbol_id)
        protection_scores = {row[0]: row[1] for row in protection_scores}
        autism_scores = self._get_autism_scores(symbol_id)
        autism_scores = {row[0]: row[1] for row in autism_scores}
        variant_counts_rows = self._get_variant_counts(symbol_id)
        variant_counts = dict()
        for row in variant_counts_rows:
            study_name = row[0]
            person_set = row[1]
            effect_type = row[2]
            count = row[3]

            if study_name not in variant_counts:
                variant_counts[study_name] = dict()

            if person_set not in variant_counts[study_name]:
                variant_counts[study_name][person_set] = dict()

            variant_counts[study_name][person_set][effect_type] = count

        return AGPStatistic(
            gene_symbol, sets_in, protection_scores,
            autism_scores, variant_counts
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
            s = s.order_by(query_order_func(sort_by))

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
                "set_name",
                String(64),
                nullable=False,
                unique=True,
                index=True,
            )
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
                    [{'set_name': s} for s in sets]
                )
            )

    def _populate_studies_table(self, studies):
        with self.engine.connect() as connection:
            connection.execute(
                insert(self.studies).values(
                    [{'study_id': s} for s in studies]
                )
            )

    def _build_autism_scores_table(self):
        self.autism_scores = Table(
            "autism_scores",
            self.metadata,
            Column("id", Integer(), primary_key=True),
            Column("symbol_id", ForeignKey("gene_symbols.id")),
            Column("score_name", String(64), nullable=False),
            Column("score_value", Float())
        )

    def _build_protection_scores_table(self):
        self.protection_scores = Table(
            "protection_scores",
            self.metadata,
            Column("id", Integer(), primary_key=True),
            Column("symbol_id", ForeignKey("gene_symbols.id")),
            Column("score_name", String(64), nullable=False),
            Column("score_value", Float())
        )

    def _build_variant_counts_table(self):
        self.variant_counts = Table(
            "variant_counts",
            self.metadata,
            Column("id", Integer(), primary_key=True),
            Column("symbol_id", ForeignKey("gene_symbols.id")),
            Column("study_id", ForeignKey("studies.study_id")),
            Column("people_group", String(64), nullable=False),
            Column("effect_type", String(64), nullable=False),
            Column("count", Integer())
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
        for gs in self.configuration["gene_sets"]:
            columns[gs] = Column(gs, Integer())

        for ps in self.configuration["protection_scores"]:
            col = f"protection_{ps}"
            columns[col] = Column(col, Float())

        for aus in self.configuration["autism_scores"]:
            col = f"autism_{aus}"
            columns[col] = Column(col, Float())

        for dataset_id, dataset in self.configuration["datasets"].items():
            config_section = self.configuration["datasets"][dataset_id]
            for person_set in config_section["person_sets"]:
                for effect_type in config_section["effects"]:
                    column_name = f"{dataset_id}_{person_set}_{effect_type}"
                    columns[column_name] = Column(column_name, Float())
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

    def generate_cache_table(self, regenerate=False):
        if not regenerate:
            self.drop_cache_table()
            self.cache_table = self._create_db_cache_table()
            self.metadata.create_all(tables=[self.cache_table])
        else:
            self._clear_cache_table()
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

        for gs in self.configuration["gene_sets"]:
            set_alias = gs
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
                    table_alias.c.set_id == gene_set_ids[gs]
                ),
                isouter=True
            )

            select_cols.append(table_alias.c.present.label(set_alias))

        for ps in self.configuration["protection_scores"]:
            score_alias = f"protection_{ps}"
            table_alias = aliased(
                self.protection_scores,
                score_alias
            )
            left = current_join
            if left is None:
                left = self.gene_symbols

            current_join = join(
                left, table_alias,
                and_(
                    self.gene_symbols.c.id == table_alias.c.symbol_id,
                    table_alias.c.score_name == ps
                )
            )

            select_cols.append(table_alias.c.score_value.label(score_alias))

        for aus in self.configuration["autism_scores"]:
            score_alias = f"autism_{aus}"
            table_alias = aliased(
                self.autism_scores,
                score_alias
            )
            left = current_join
            if left is None:
                left = self.gene_symbols

            current_join = join(
                left, table_alias,
                and_(
                    self.gene_symbols.c.id == table_alias.c.symbol_id,
                    table_alias.c.score_name == aus
                )
            )

            select_cols.append(table_alias.c.score_value.label(score_alias))

        for dataset_id, dataset in self.configuration["datasets"].items():
            config_section = self.configuration["datasets"][dataset_id]
            db_study_id = study_ids[dataset_id]
            for person_set in config_section["person_sets"]:
                for effect_type in config_section["effects"]:
                    count_alias = f"{dataset_id}_{person_set}_{effect_type}"
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
                            table_alias.c.people_group == person_set,
                            table_alias.c.effect_type == effect_type
                        )
                    )
                    select_cols.append(
                        table_alias.c.count.label(count_alias)
                    )

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
        self._build_autism_scores_table()
        self._build_protection_scores_table()
        self._build_variant_counts_table()
        if clear:
            self.metadata.drop_all()
        self.metadata.create_all()

    def clear_all_tables(self):
        with self.engine.connect() as connection:
            connection.execute(delete(self.variant_counts))
            connection.execute(delete(self.gene_symbol_sets))
            connection.execute(delete(self.protection_scores))
            connection.execute(delete(self.autism_scores))
            connection.execute(delete(self.studies))
            connection.execute(delete(self.gene_symbols))
            connection.execute(delete(self.gene_sets))

    def populate_data_tables(self, studies):
        gene_sets = self.configuration["gene_sets"]
        self._populate_gene_sets_table(gene_sets)
        self._populate_studies_table(studies)

    def insert_agp(self, agp):
        with self.engine.connect() as connection:
            connection.execute(
                insert(self.gene_symbols).values(symbol_name=agp.gene_symbol)
            )
            symbol_id = self._get_gene_symbol_id(agp.gene_symbol)
            for name, value in agp.protection_scores.items():
                connection.execute(
                    insert(self.protection_scores).values(
                        symbol_id=symbol_id,
                        score_name=name,
                        score_value=value
                    )
                )
            for name, value in agp.autism_scores.items():
                connection.execute(
                    insert(self.autism_scores).values(
                        symbol_id=symbol_id,
                        score_name=name,
                        score_value=value
                    )
                )
            gene_sets = self._get_gene_sets()
            for gs_row in gene_sets:
                if gs_row["set_name"] in agp.gene_sets:
                    present = 1
                else:
                    present = 0
                set_id = gs_row["id"]
                connection.execute(
                    insert(self.gene_symbol_sets).values(
                        symbol_id=symbol_id,
                        set_id=set_id,
                        present=present
                    )
                )

            study_ids = self._get_study_ids()
            for study, counts in agp.variant_counts.items():
                study_id = study_ids[study]
                for people_group, effects in counts.items():
                    for effect_type, count in effects.items():
                        connection.execute(
                            insert(self.variant_counts).values(
                                symbol_id=symbol_id,
                                study_id=study_id,
                                people_group=people_group,
                                effect_type=effect_type,
                                count=count
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
                    for name, value in agp.protection_scores.items():
                        connection.execute(
                            insert(self.protection_scores).values(
                                symbol_id=symbol_id,
                                score_name=name,
                                score_value=value
                            )
                        )
                    for name, value in agp.autism_scores.items():
                        connection.execute(
                            insert(self.autism_scores).values(
                                symbol_id=symbol_id,
                                score_name=name,
                                score_value=value
                            )
                        )
                    for gene_set, set_id in gene_set_ids.items():
                        set_id = gene_set_ids[gene_set]
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

                    for study, counts in agp.variant_counts.items():
                        study_id = study_ids[study]
                        for people_group, effects in counts.items():
                            for effect_type, count in effects.items():
                                connection.execute(
                                    insert(self.variant_counts).values(
                                        symbol_id=symbol_id,
                                        study_id=study_id,
                                        people_group=people_group,
                                        effect_type=effect_type,
                                        count=count
                                    )
                                )

                    if idx % 25 == 0:
                        logger.info(f"Inserted {idx}/{agp_count} AGPs into DB")
                logger.info("Done!")
