
import os
import pathlib

import duckdb

from gain.genomic_resources.cli import _create_contents_db
from gain.genomic_resources.fsspec_protocol import (
    FsspecReadWriteProtocol,
    build_fsspec_protocol,
)


def regenerate_grr_contents(proto: FsspecReadWriteProtocol) -> None:
    """Regenerate the .CONTENTS.duckdb file for the given GRR path."""

    db_filepath = os.path.join(proto.url, ".CONTENTS.duckdb")

    if os.path.exists(db_filepath):
        os.remove(db_filepath)

    contents = proto.load_contents()
    _create_contents_db(proto, contents)


def build_fts_query(term: str) -> str:
    """Build a full-text search query for the given term."""

    return f"""
    SELECT full_id FROM
    (SELECT
        full_id,
        COALESCE(
            fts_main_contents.match_bm25(full_id,'{term}'), 0) +
        COALESCE(
            fts_main_contents_first.match_bm25(full_id,'{term}'), 0) as score,
        FROM contents WHERE score > 0 ORDER BY score desc)
    """  # noqa: S608


def build_and_query(*terms: str) -> str:
    term_queries = [build_fts_query(term) for term in terms]
    return " INTERSECT ".join(term_queries)


def build_or_query(*terms: str) -> str:
    term_queries = [build_fts_query(term) for term in terms]
    return " UNION ".join(term_queries)


def build_not_query(term: str) -> str:
    return f"""
    SELECT full_id FROM
    (SELECT
        full_id,
        COALESCE(
            fts_main_contents_first.match_bm25(full_id,'{term}'), 0) as score,
        FROM contents WHERE score == 0)
    """  # noqa: S608


def execute_grr_search(
    proto: FsspecReadWriteProtocol,
    query: str,
) -> None:
    """Search the GRR contents using the .CONTENTS.duckdb file."""

    duckdb.register_filesystem(proto.filesystem)

    db_filepath = os.path.join(proto.url, ".CONTENTS.duckdb")

    with duckdb.connect(db_filepath) as conn:
        result = conn.execute(query).fetchall()
        for r in result:
            print(*r)
        print(f"Total matches: {len(result)}")


def main() -> None:
    """Main function to demonstrate the GRR search functionality."""
    grr_path = pathlib.Path(
        "/home/lubo/Work/seq-pipeline/data2/encode_grr/grr_encode")
    grr_path = pathlib.Path(
        "/home/lubo/Work/seq-pipeline/local/grr")

    proto = build_fsspec_protocol("search_grr", str(grr_path))
    assert isinstance(proto, FsspecReadWriteProtocol)

    query = build_and_query("gencode", "hg38", "gene_models")
    print(query)
    execute_grr_search(proto, query)


if __name__ == "__main__":
    main()
