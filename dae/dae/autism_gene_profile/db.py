from dae.autism_gene_profile.statistic import AGPStatistic
from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.sql import select, insert, join, delete


class AutismGeneProfileDB:
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.metadata = MetaData()
        self.engine = create_engine("sqlite:///{}".format(dbfile))
        self.configuration = None
        self.build_gene_profile_db()

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

    def _get_study_ids(self):
        s = select(self.studies.c)
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

    def _get_gene_symbol_sets(self, gene_symbol_id):
        j = join(
            self.gene_symbol_sets, self.gene_sets,
            self.gene_symbol_sets.c.set_id == self.gene_sets.c.id
        )
        s = select([self.gene_sets.c.set_name]).select_from(j).where(
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

    def get_agp(self, gene_symbol):
        symbol_id = self._get_gene_symbol_id(gene_symbol)
        sets_in = self._get_gene_symbol_sets(symbol_id)
        sets_in = [row[0] for row in sets_in]
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
            Column("set_id", ForeignKey("gene_sets.id"))
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

    def build_gene_profile_db(self):
        self.metadata.drop_all(self.engine)
        self._build_gene_symbols_table()
        self._build_gene_sets_table()
        self._build_gene_symbol_sets_table()
        self._build_studies_table()
        self._build_autism_scores_table()
        self._build_protection_scores_table()
        self._build_variant_counts_table()
        self.metadata.create_all(self.engine)

    def clear_all_tables(self):
        with self.engine.connect() as connection:
            connection.execute(delete(self.variant_counts))
            connection.execute(delete(self.gene_symbol_sets))
            connection.execute(delete(self.protection_scores))
            connection.execute(delete(self.autism_scores))
            connection.execute(delete(self.studies))
            connection.execute(delete(self.gene_symbols))
            connection.execute(delete(self.gene_sets))

    def populate_data_tables(self, gpf_instance):
        gene_sets = gpf_instance.gene_sets_db.get_gene_set_ids("main")
        self._populate_gene_sets_table(gene_sets)
        studies = gpf_instance.get_genotype_data_ids()
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
            for gene_set in agp.gene_sets:
                gene_set_db = self._get_gene_set(gene_set)
                if not gene_set_db:
                    connection.execute(
                        insert(self.gene_sets).values(
                            set_name=gene_set
                        )
                    )
                    gene_set_db = self._get_gene_set(gene_set)
                set_id = gene_set_db[0]
                connection.execute(
                    insert(self.gene_symbol_sets).values(
                        symbol_id=symbol_id,
                        set_id=set_id
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

    def get_full_configuration(self, gpf_instance):
        if not self.configuration:
            self.configuration = \
                gpf_instance._autism_gene_profile_config.to_dict()
            s = select([self.gene_sets.c.set_name])
            with self.engine.connect() as connection:
                sets = connection.execute(s).fetchall()
            self.configuration["gene_lists"] = [row[0] for row in sets]
            for dataset in self.configuration["datasets"]:
                dataset_dict = self.configuration["datasets"][dataset]
                person_sets = dataset_dict["person_sets"]
                dataset_dict["person_sets"] = [
                    ps["set_name"] for ps in person_sets
                ]
        return self.configuration
