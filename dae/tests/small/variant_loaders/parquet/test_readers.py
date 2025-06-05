# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pyarrow as pa
import pyarrow.parquet as pq

from dae.variants_loaders.parquet.loader import MultiReader, Reader


def test_reader(tmp_path: pathlib.Path) -> None:
    file_path = str(tmp_path / "file_a.parquet")
    pq.write_table(pa.table({"bucket_index": [0, 0, 0, 1, 1, 1],
                             "summary_index": [1, 1, 2, 1, 2, 2]}),
                            file_path)
    reader = Reader(file_path, columns=("bucket_index", "summary_index"))
    assert list(reader) == [
        [{"bucket_index": 0, "summary_index": 1},
         {"bucket_index": 0, "summary_index": 1}],
        [{"bucket_index": 0, "summary_index": 2}],
        [{"bucket_index": 1, "summary_index": 1}],
        [{"bucket_index": 1, "summary_index": 2},
         {"bucket_index": 1, "summary_index": 2}],
    ]


def test_multi_reader(tmp_path: pathlib.Path) -> None:
    file_path_a = str(tmp_path / "file_a.parquet")
    pq.write_table(pa.table({"bucket_index": [0, 0, 0, 1, 1, 1],
                             "summary_index": [1, 1, 2, 1, 2, 2]}),
                            file_path_a)
    file_path_b = str(tmp_path / "file_b.parquet")
    pq.write_table(pa.table({"bucket_index": [0, 0, 0, 1, 1, 1],
                             "summary_index": [2, 2, 3, 2, 3, 3]}),
                            file_path_b)
    file_path_c = str(tmp_path / "file_c.parquet")
    pq.write_table(pa.table({"bucket_index": [0, 0, 0, 1, 1, 1],
                             "summary_index": [3, 3, 4, 3, 4, 4]}),
                            file_path_c)
    reader = MultiReader((file_path_a, file_path_b, file_path_c),
                         columns=("bucket_index", "summary_index"))
    assert list(reader) == [
        # 0,1
        [{"bucket_index": 0, "summary_index": 1},
         {"bucket_index": 0, "summary_index": 1}],
        # 0,2
        [{"bucket_index": 0, "summary_index": 2},
         {"bucket_index": 0, "summary_index": 2},
         {"bucket_index": 0, "summary_index": 2}],
        # 0,3
        [{"bucket_index": 0, "summary_index": 3},
         {"bucket_index": 0, "summary_index": 3},
         {"bucket_index": 0, "summary_index": 3}],
        # 0,4
        [{"bucket_index": 0, "summary_index": 4}],
        # 1,1
        [{"bucket_index": 1, "summary_index": 1}],
        # 1,2
        [{"bucket_index": 1, "summary_index": 2},
         {"bucket_index": 1, "summary_index": 2},
         {"bucket_index": 1, "summary_index": 2}],
        # 1,3
        [{"bucket_index": 1, "summary_index": 3},
         {"bucket_index": 1, "summary_index": 3},
         {"bucket_index": 1, "summary_index": 3}],
        # 1,4
        [{"bucket_index": 1, "summary_index": 4},
         {"bucket_index": 1, "summary_index": 4}],
    ]
