#!/usr/bin/env python
import time
import argparse
import logging
from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.sql import select, insert

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants.attributes import Inheritance

logger = logging.getLogger(__name__)


class AutismGeneProfileDB:
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.metadata = MetaData()
        self.engine = create_engine("sqlite:///{}".format(dbfile))

    def _get_autism_scores(self, gene_symbol_id):
        return select(self.autism_scores).where(
            self.autism_scores.c.symbol_id == gene_symbol_id,
        )

    def _get_protection_scores(self, gene_symbol_id):
        return select(self.protection_scores).where(
            self.protection_scores.c.symbol_id == gene_symbol_id,
        )

    def _get_variant_counts(self, gene_symbol_id):
        return select(self.variant_counts).where(
            self.variant_counts.c.symbol_id == gene_symbol_id,
        )

    def _get_gene_symbol_id(self, gene_symbol):
        s = select(self.gene_symbols).where(
            self.gene_symbols.c.symbol_name == gene_symbol,
        )
        with self.engine.connect() as connection:
            gene_symbols = connection.execute(s).fetchall()
        return gene_symbols[0].id

    def _get_gene_symbols(self):
        s = select([self.gene_symbols])
        with self.engine.connect() as connection:
            gene_symbols = connection.execute(s).fetchall()
        return [gs.symbol_name for gs in gene_symbols]

    def get_profiles(self):
        pass

    def _build_gene_symbols_table(self):
        self.gene_symbols = Table(
            "gene_symbols",
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
            Column("id", Integer(), primary_key=True),
            Column(
                "set_name",
                String(64),
                nullable=False,
                unique=True,
                index=True,
            ),
        )

    def _build_gene_sets_symbols_table(self):
        self.gene_sets_symbols = Table(
            "gene_sets_symbols",
            Column("id", Integer(), primary_key=True),
            Column("symbol_id", ForeignKey("gene_symbols.id")),
            Column("set_id", ForeignKey("gene_sets.id")),
        )

    def _populate_gene_sets_table(self, sets):
        with self.engine.connect() as connection:
            connection.execute(
                self.gene_sets.insert(),
                [{'set_name': s} for s in sets]
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
            Column("effect_type", String(64), nullable=False)
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
        self._build_gene_symbols_table()
        self._build_studies_table()
        self._build_autism_scores_table()
        self._build_protection_scores_table()
        self._build_variant_counts_table()

    def insert_agp(self, agp):
        insert(self.gene_symbols).values(symbol_name=agp.gene_symbol)
        symbol_id = select(self.gene_symbols).where(
            self.gene_symbols.c.symbol_name == agp.gene_symbol)
        for name, value in agp.protection_scores.items():
            insert(self.protection_scores).values(
                symbol_id=symbol_id, score_name=name, score_value=value)
        for name, value in agp.autism_scores.items():
            insert(self.autism_scores).values(
                symbol_id=symbol_id, score_name=name, score_value=value)


class AutismGeneProfile:
    def __init__(
            self, gene_symbol, gene_sets, protection_scores,
            autism_scores, variant_counts):
        self.gene_symbol = gene_symbol
        self.gene_sets = gene_sets
        self.protection_scores = protection_scores
        self.autism_scores = autism_scores
        self.variant_counts = variant_counts


def generate_agp(gpf_instance, gene_symbol):
    gene_weights_db = gpf_instance.gene_weights_db
    config = gpf_instance._autism_gene_profile_config
    autism_scores = dict()
    protection_scores = dict()

    gene_sets = gpf_instance.gene_sets_db.get_all_gene_sets("main")
    sets_in = []
    for gs in gene_sets:
        if gene_symbol in gs["syms"]:
            sets_in.append(gs["name"])

    for score in config.autism_scores:
        gw = gene_weights_db.get_gene_weight(score)
        value = gw.get_gene_value(gene_symbol)
        autism_scores[score] = value

    for score in config.protection_scores:
        gw = gene_weights_db.get_gene_weight(score)
        value = gw.get_gene_value(gene_symbol)
        protection_scores[score] = value

    variant_counts = dict()

    print(config.datasets.items())
    for dataset_id, filters in config.datasets.items():
        genotype_data = gpf_instance.get_genotype_data(dataset_id)
        for ps in filters.person_sets:
            person_set_query = (
                ps.collection_name,
                [ps.set_name]
            )
            for effect in filters.effects:
                counts = variant_counts.get(ps.set_name)
                if not counts:
                    variant_counts[ps.set_name] = dict()
                    counts = variant_counts[ps.set_name]
                fvars = genotype_data.query_variants(
                    genes=[gene_symbol],
                    person_set_collection=person_set_query,
                    effect_types=[effect],
                )
                counts[effect] = len(list(fvars))

    return AutismGeneProfile(
        gene_symbol, sets_in, protection_scores,
        autism_scores, variant_counts
    )


def main(gpf_instance=None, argv=None):
    description = "Generate autism gene profile statistics tool"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose', '-V', action='count', default=0)
    parser.add_argument("--dbfile", default="agpdb")

    args = parser.parse_args(argv)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    start = time.time()
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    config = gpf_instance._autism_gene_profile_config
    gene_symbols = set()
    for gene_set_name in config.gene_sets:
        gene_set = gpf_instance.gene_sets_db.get_gene_set(
            "main", gene_set_name)
        gene_symbols.union(set(gene_set["syms"]))
    output = []
    for sym in gene_symbols:
        output.append(generate_agp(gpf_instance, sym))
    print(output)
    duration = time.time() - start
    print(duration)


if __name__ == "__main__":
    main()
