# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from typing import cast

import pytest
import pytest_mock
from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.genomic_position_table import (
    VCFGenomicPositionTable,
)
from dae.genomic_resources.genomic_position_table.line import (
    BigWigLine,
    Line,
    VCFLine,
)
from dae.genomic_resources.genomic_scores import (
    AlleleScore,
    GenomicScore,
    ScoreLine,
    build_score_from_resource,
    build_score_from_resource_id,
)
from dae.genomic_resources.histogram import (
    CategoricalHistogramConfig,
    NullHistogram,
    NullHistogramConfig,
    NumberHistogram,
    NumberHistogramConfig,
)
from dae.genomic_resources.implementations.genomic_scores_impl import (
    build_score_implementation_from_resource,
)
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, GenomicResource
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    build_filesystem_test_resource,
    build_inmemory_test_repository,
    build_inmemory_test_resource,
    convert_to_tab_separated,
    setup_directories,
    setup_genome,
    setup_tabix,
    setup_vcf,
)
from dae.task_graph.graph import TaskGraph
from pysam import VariantRecord


def build_simple_position_score_resource(
        extra_files: dict[str, str] | None = None) -> GenomicResource:
    base_content = {
        GR_CONF_FILE_NAME: textwrap.dedent("""
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
        """),
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos_end score
            1     10        10      0.1
            1     20        20      0.2
        """),
    }
    if extra_files:
        base_content.update(extra_files)
    return build_inmemory_test_resource(base_content)


@pytest.fixture
def vcf_score(tmp_path: pathlib.Path) -> AlleleScore:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": textwrap.dedent("""
                type: allele_score
                table:
                    filename: data.vcf.gz
                    format: vcf_info
            """),
        })
    setup_vcf(
        tmp_path / "data.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
##INFO=<ID=B,Number=.,Type=Integer,Description="Score B">
##INFO=<ID=C,Number=R,Type=String,Description="Score C">
##INFO=<ID=D,Number=A,Type=String,Description="Score D">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chr1   2   .  A   .   .    .       A=0;B=01,02,03;C=c01
chr1   5   .  A   T   .    .       A=1;B=11,12,13;C=c11,c12;D=d11
chr1   15   .  A   T,G   .    .       A=2;B=21,22;C=c21,c22,c23;D=d21,d22
chr1   30   .  A   T,G,C   .    .      A=3;B=31;C=c31,c32,c33,c34;D=d31,d32,d33
    """),
    )
    res = build_filesystem_test_resource(tmp_path)
    score = build_score_from_resource(res)
    return cast(AlleleScore, score)


def test_scoreline_init(mocker: pytest_mock.MockerFixture) -> None:
    raw_line = ("chr1", 1, 10, 0.123)
    assert ScoreLine(Line(raw_line), {})
    assert ScoreLine(VCFLine(mocker.Mock(spec=VariantRecord), None), {})
    assert ScoreLine(BigWigLine(raw_line), {})


def test_default_annotation_pre_normalize_validates() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
              - id: phastCons100way
                type: float
                desc: "The phastCons computed over the tree of 100 \
                       verterbrate species"
                name: s1
            default_annotation:
              attributes:
                - phastCons100way""",
        "data.mem": """
            chrom  pos_begin  s1
            1      10         0.02
            1      11         0.03
            1      15         0.46
            2      8          0.01
            """,
    })
    assert res is not None
    assert res.get_type() == "position_score"


def test_default_annotation_auto_includes_all_scores() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score1
                  type: float
                  name: score1
                - id: score2
                  type: float
                  name: score2
        """,
        "data.mem": """
            chrom  pos_begin  score1  score2
            1      10         0.1     0.2
        """,
    })

    score = build_score_from_resource(res)
    score.open()

    attributes = score.get_default_annotation_attributes()
    assert attributes == [
        {"source": "score1", "name": "score1"},
        {"source": "score2", "name": "score2"},
    ]

    assert score.get_default_annotation_attribute("score1") == "score1"
    assert score.get_default_annotation_attribute("score2") == "score2"
    assert score.get_default_annotation_attribute("missing") is None


def test_default_annotation_custom_names() -> None:
    res: GenomicResource = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score1
                  type: float
                  name: score1
                - id: score2
                  type: float
                  name: score2
            default_annotation:
                - source: score1
                  name: primary_score
                - source: score1
                  name: secondary_score
                - source: score2
        """,
        "data.mem": """
            chrom  pos_begin  score1  score2
            1      10         0.1     0.2
        """,
    })

    score = build_score_from_resource(res)
    score.open()

    attributes = score.get_default_annotation_attributes()
    assert attributes == [
        {"source": "score1", "name": "primary_score"},
        {"source": "score1", "name": "secondary_score"},
        {"source": "score2"},
    ]

    assert (
        score.get_default_annotation_attribute("score1")
        == "primary_score,secondary_score"
    )
    assert score.get_default_annotation_attribute("score2") == "score2"
    assert score.get_default_annotation_attribute("score3") is None


def test_vcf_tables_autogenerate_scoredefs(vcf_score: AlleleScore) -> None:
    assert isinstance(vcf_score.table, VCFGenomicPositionTable)
    assert set(vcf_score.score_definitions.keys()) == {"A", "B", "C", "D"}
    assert vcf_score.score_definitions["A"].desc == "Score A"
    assert vcf_score.score_definitions["A"].value_parser is None


def test_vcf_tables_can_override_autogenerated_scoredefs(
        tmp_path: pathlib.Path) -> None:
    root_path = tmp_path
    setup_directories(
        root_path / "grr",
        {
            "tmp": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: allele_score
                    table:
                        filename: data.vcf.gz
                    scores:
                    - id: A
                      name: A
                      type: float
                      desc: Score A, but overriden
                """),
            },
        },
    )
    setup_vcf(
        root_path / "grr" / "tmp" / "data.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
##INFO=<ID=B,Number=1,Type=Float,Description="Score B">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chr1   5   .  A   T   .    .       A=1;B=2.5
    """))
    proto = build_fsspec_protocol("testing", str(root_path / "grr"))
    score = build_score_from_resource(proto.get_resource("tmp"))
    assert isinstance(score.table, VCFGenomicPositionTable)
    assert set(score.score_definitions.keys()) == {"A"}
    assert score.score_definitions["A"].desc == "Score A, but overriden"
    assert score.score_definitions["A"].value_parser is float


def test_vcf_tables_merge_vcf_scores(tmp_path: pathlib.Path) -> None:
    root_path = tmp_path
    setup_directories(
        root_path / "grr",
        {
            "merge": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: allele_score
                    merge_vcf_scores: true
                    table:
                        filename: data.vcf.gz
                    scores:
                    - id: A
                      name: A
                      type: float
                      desc: Score A, but overriden
                """),
            },
        },
    )
    setup_vcf(
        root_path / "grr" / "merge" / "data.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
##INFO=<ID=B,Number=1,Type=Float,Description="Score B">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chr1   5   .  A   T   .    .       A=1;B=2.5
        """),
    )
    proto = build_fsspec_protocol("testing", str(root_path / "grr"))
    score = build_score_from_resource(proto.get_resource("merge"))
    assert isinstance(score.table, VCFGenomicPositionTable)
    assert set(score.score_definitions.keys()) == {"A", "B"}
    assert score.score_definitions["A"].desc == "Score A, but overriden"
    assert score.score_definitions["A"].value_parser is float
    assert score.score_definitions["B"].desc == "Score B"
    assert score.score_definitions["B"].value_parser is None


def test_score_definition_via_index_headerless_tabix(
        tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": """
                type: position_score
                table:
                  filename: data.txt.gz
                  format: tabix
                  header_mode: none
                  chrom:
                    index: 0
                  pos_begin:
                    index: 1
                  pos_end:
                    index: 2
                scores:
                - id: piscore
                  index: 3
                  type: float
            """,
        })
    setup_tabix(
        tmp_path / "data.txt.gz",
        "1     10        12       3.14",
        seq_col=0, start_col=1, end_col=2)
    res = build_filesystem_test_resource(tmp_path)
    score = build_score_from_resource(res)
    score.open()
    score_line = next(score._fetch_lines("1", 10, 12))
    assert len(score.score_definitions) == 1
    assert "piscore" in score.score_definitions
    assert score_line.get_available_scores() == ("piscore",)
    assert score_line.get_score("piscore") == 3.14


def test_score_definition_list_header_tabix(tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": """
                type: allele_score
                table:
                    filename: data.txt.gz
                    format: tabix
                    header_mode: list
                    header:
                    - chrom
                    - start
                    - stop
                    - reference
                    - alt
                    - score
                    pos_begin:
                      name: start
                    pos_end:
                      name: stop
                    reference:
                      name: reference
                    alternative:
                      name: alt
                scores:
                - id: piscore
                  name: score
                  type: float
            """,
        })
    setup_tabix(
        tmp_path / "data.txt.gz",
        "1     10        12         A         G     3.14",
        seq_col=0, start_col=1, end_col=2)
    res = build_filesystem_test_resource(tmp_path)
    score = build_score_from_resource(res)
    score.open()
    score_line = next(score._fetch_lines("1", 10, 12))
    assert len(score.score_definitions) == 1
    assert "piscore" in score.score_definitions
    assert score_line.get_available_scores() == ("piscore",)
    assert score_line.chrom == "1"
    assert score_line.pos_begin == 10
    assert score_line.pos_end == 12
    assert score_line.ref == "A"
    assert score_line.alt == "G"
    assert score_line.get_score("piscore") == 3.14


def test_forbid_column_names_in_scores_when_no_header_configured() -> None:
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                header_mode: none
                filename: data.mem
                chrom:
                    index: 0
                pos_begin:
                    index: 1
            scores:
            - id: c2
              name: this_doesnt_make_sense
              type: float""",
        "data.mem": convert_to_tab_separated("""
            1   10  12  3.14
        """),
    })
    with pytest.raises(AssertionError) as excinfo:
        build_score_from_resource(res).open()
    assert str(excinfo.value) == ("Cannot configure score columns by name"
                                  " when header_mode is 'none'!")


def test_raise_error_when_missing_column_name_in_header() -> None:
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                pos_begin:
                    name: pos2
            scores:
            - id: c2
              name: this_doesnt_exist_in_header
              type: float""",
        "data.mem": convert_to_tab_separated(
            """
            chrom pos pos2 c2
            1     10  12   3.14
            """),
    })
    with pytest.raises(AssertionError):
        build_score_from_resource(res).open()


def test_raise_error_when_missing_column_name_in_header_as_list() -> None:
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                header_mode: list
                header: ["chrom", "pos", "pos2", "score"]
                filename: data.mem
                pos_begin:
                    name: pos2
            scores:
            - id: c2
              name: this_doesnt_exist_in_header
              type: float""",
        "data.mem": convert_to_tab_separated("""
            1   10  12  3.14
        """),
    })
    with pytest.raises(AssertionError):
        build_score_from_resource(res).open()


def test_vcf_check_for_missing_score_columns(tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": textwrap.dedent("""
                type: allele_score
                table:
                  filename: data.vcf.gz
                scores:
                - id: A
                  name: NO_SUCH_SCORE_IN_HEADER
                  type: float
            """),
        })
    setup_vcf(
        tmp_path / "data.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chr1   5   .  A   T   .    .       A=1
    """))
    res = build_filesystem_test_resource(tmp_path)
    with pytest.raises(AssertionError):
        build_score_from_resource(res).open()


def test_line_score_value_parsing(tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": """
                type: position_score
                table:
                  filename: data.txt.gz
                  format: tabix
                scores:
                - id: c2
                  name: c2
                  type: float
            """,
        })
    setup_tabix(
        tmp_path / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end    c2
        1     10        12       3.14
        1     15        20       4.14
        1     21        30       5.14
        """, seq_col=0, start_col=1, end_col=2)
    res = build_filesystem_test_resource(tmp_path)
    score = build_score_from_resource(res)
    score.open()
    result = [line.get_score("c2") for line in score._fetch_lines("1", 10, 30)]
    assert result == [3.14, 4.14, 5.14]


def test_genomic_score_chrom_mapping(tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": """
                type: position_score
                table:
                  filename: data.txt.gz
                  chrom_mapping:
                    add_prefix: chr
                  format: tabix
                scores:
                - id: c2
                  name: c2
                  type: float
            """,
        })
    setup_tabix(
        tmp_path / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end    c2
        1     10        12       3.14
        1     15        20       4.14
        1     21        30       5.14
        """, seq_col=0, start_col=1, end_col=2)
    res = build_filesystem_test_resource(tmp_path)
    impl = build_score_implementation_from_resource(res)
    score = impl.score
    score.open()
    result = impl._get_chrom_regions(1_000_000)
    assert result[0].chrom == "chr1"


def test_genomic_score_chrom_mapping_with_genome(
        tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path, {
            "one": {
                "genomic_resource.yaml": """
                    type: position_score
                    table:
                      filename: data.txt.gz
                      chrom_mapping:
                        add_prefix: chr
                      format: tabix
                    scores:
                    - id: c2
                      name: c2
                      type: float
                    meta:
                      labels:
                        reference_genome: two
                """,
            },
            "two": {
                "genomic_resource.yaml": "{type: genome, filename: chr.fa}",
            },
        })
    setup_tabix(
        tmp_path / "one" / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end    c2
        1     10        12       3.14
        1     15        20       4.14
        1     21        30       5.14
        """, seq_col=0, start_col=1, end_col=2)
    setup_genome(tmp_path / "two" / "chr.fa", textwrap.dedent("""
            >chr1
            NNACCCAAAC
            GGGCCTTCCN
            GGGCCTTCCN
            GGGCCTTCCN
            GGGCCTTCCN
    """))
    repo = build_filesystem_test_repository(tmp_path)
    res = repo.get_resource("one")
    impl = build_score_implementation_from_resource(res)
    score = impl.score
    score.open()
    result = impl._get_chrom_regions(1_000_000)
    assert result[0].chrom == "chr1"


def test_line_score_na_values(tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": """
                type: position_score
                table:
                  filename: data.txt.gz
                  format: tabix
                scores:
                - id: c2
                  name: c2
                  type: float
                  na_values:
                  - "4.14"
                  - "5.14"
            """,
        })
    setup_tabix(
        tmp_path / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end    c2
        1     10        12       3.14
        1     15        20       4.14
        1     21        30       5.14
        """, seq_col=0, start_col=1, end_col=2)
    res = build_filesystem_test_resource(tmp_path)

    score = build_score_from_resource(res)
    score.open()
    result = [line.get_score("c2") for line in score._fetch_lines("1", 10, 30)]
    assert result == [3.14, None, None]


def test_line_get_available_score_columns(vcf_score: AlleleScore) -> None:
    vcf_score.open()
    score_line = next(vcf_score._fetch_lines("chr1", 2, 30))
    assert set(score_line.get_available_scores()) == {"A", "B", "C", "D"}


def test_vcf_tuple_scores_autoconcat_to_string(vcf_score: AlleleScore) -> None:
    vcf_score.open()
    results = tuple(
        (r.chrom, r.pos_begin, r.pos_end, r.get_score("B"))
        for r in vcf_score._fetch_lines("chr1", 2, 30)
    )
    assert results == (
        ("chr1", 2, 2, "1|2|3"),
        ("chr1", 5, 5, "11|12|13"),
        ("chr1", 15, 15, "21|22"),
        ("chr1", 15, 15, "21|22"),
        ("chr1", 30, 30, "31"),
        ("chr1", 30, 30, "31"),
        ("chr1", 30, 30, "31"),
    )


def test_vcf_tables_can_select_subset_of_autogenerated_scoredefs(
    tmp_path: pathlib.Path,
) -> None:
    root_path = tmp_path
    setup_directories(
        root_path / "grr",
        {
            "tmp": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: allele_score
                    table:
                        filename: data.vcf.gz
                    scores:
                    - id: A
                    - id: C
                """),
            },
        },
    )
    setup_vcf(
        root_path / "grr" / "tmp" / "data.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
##INFO=<ID=B,Number=1,Type=Integer,Description="Score B">
##INFO=<ID=C,Number=.,Type=String,Description="Score C">
##INFO=<ID=D,Number=.,Type=String,Description="Score D">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chr1   5   .  A   T   .    .       A=1;C=c11,c12;D=d11
    """))
    proto = build_fsspec_protocol("testing", str(root_path / "grr"))
    score = build_score_from_resource(proto.get_resource("tmp"))
    assert isinstance(score.table, VCFGenomicPositionTable)
    assert set(score.score_definitions.keys()) == {"A", "C"}
    assert score.score_definitions["A"].desc == "Score A"
    assert score.score_definitions["A"].value_type == "int"
    assert score.score_definitions["C"].desc == "Score C"
    assert score.score_definitions["C"].value_type == "str"


def test_score_definition_new_configuration_fields(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": """
                type: position_score
                table:
                  filename: data.txt.gz
                  format: tabix
                  header_mode: list
                  header: ["chrom", "pos", "pos2", "score", "score2"]
                  chrom:
                    column_index: 0
                  pos_begin:
                    column_index: 1
                  pos_end:
                    column_name: pos2
                scores:
                - id: piscore
                  column_index: 3
                  type: float
                - id: 2piscore
                  column_name: score2
                  type: float
            """,
        })
    setup_tabix(
        tmp_path / "data.txt.gz",
        "1     10        12       3.14  6.28",
        seq_col=0, start_col=1, end_col=2)
    res = build_filesystem_test_resource(tmp_path)
    score = build_score_from_resource(res)
    score.open()
    assert len(score.score_definitions) == 2
    assert "piscore" in score.score_definitions
    assert "2piscore" in score.score_definitions

    score_line = next(score._fetch_lines("1", 10, 12))
    assert score_line.get_available_scores() == ("piscore", "2piscore")
    assert score_line.get_score("piscore") == 3.14
    assert score_line.get_score("2piscore") == 6.28


def test_score_definition_histograms(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": """
                type: position_score
                table:
                  filename: data.txt.gz
                  format: tabix
                  header_mode: list
                  header: ["chrom", "pos", "score1", "score2"]
                  chrom:
                    column_index: 0
                  pos_begin:
                    column_index: 1
                  pos_end:
                    column_index: 1
                scores:
                - id: score1
                  column_index: 2
                  type: str
                - id: score2
                  column_index: 3
                  type: str
                  histogram:
                    type: categorical
            """,
        })
    setup_tabix(
        tmp_path / "data.txt.gz",
        "1  10  aaa  bbb",
        seq_col=0, start_col=1, end_col=1)
    res = build_filesystem_test_resource(tmp_path)
    score = build_score_from_resource(res)
    score.open()
    assert len(score.score_definitions) == 2
    assert "score1" in score.score_definitions
    assert "score2" in score.score_definitions

    score_line = next(score._fetch_lines("1", 10, 10))
    assert score_line.get_available_scores() == ("score1", "score2")
    assert score_line.get_score("score1") == "aaa"
    assert score_line.get_score("score2") == "bbb"

    score1_def = score.score_definitions["score1"]
    assert score1_def.hist_conf is None

    score2_def = score.score_definitions["score2"]
    assert score2_def.hist_conf is not None
    assert isinstance(score2_def.hist_conf, CategoricalHistogramConfig)
    assert score2_def.hist_conf.enforce_type


def test_build_genomic_score_from_resource_id() -> None:
    grr = build_inmemory_test_repository({
        "example_score": {
            GR_CONF_FILE_NAME: """
                type: position_score
                table:
                  filename: data.mem
                scores:
                  - id: s1
                    type: float
                    name: s1
            """,
            "data.mem": """
                chrom  pos_begin  s1
                1      10         0.02
            """,
        }})
    score = build_score_from_resource_id("example_score", grr)
    score.open()
    assert score is not None
    assert list(score._fetch_region_values("1", 10, None, ["s1"])) == [
        (10, 10, [0.02])]


def test_statistics_build_tasks(tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml": """
                type: position_score
                table:
                  filename: data.txt.gz
                  format: tabix
                scores:
                - id: dummy
                  name: dummy
                  type: float
            """,
        })
    setup_tabix(
        tmp_path / "data.txt.gz",
        """
        #chrom  pos_begin  pos_end  dummy
        chr1     1         20       3.14
        chr1    21         40       3.15
        chr1    41         60       3.16
        chr2    10         20       4.14
        chr3    10         20       5.14
        """, seq_col=0, start_col=1, end_col=2)
    res = build_filesystem_test_resource(tmp_path)
    impl = build_score_implementation_from_resource(res)

    task_graph = TaskGraph()
    tasks = impl.add_statistics_build_tasks(task_graph)
    save_task = tasks[0]
    merge_task = save_task.deps[0]
    calc_tasks = merge_task.deps
    assert len(calc_tasks) == 3 + 1  # 3 hist region tasks, 1 for hist conf

    task_graph = TaskGraph()
    tasks = impl.add_statistics_build_tasks(task_graph, region_size=20)
    save_task = tasks[0]
    merge_task = save_task.deps[0]
    calc_tasks = merge_task.deps
    assert len(calc_tasks) == 9 + 1  # 9 hist region tasks, 1 for hist conf

    task_graph = TaskGraph()
    tasks = impl.add_statistics_build_tasks(task_graph, region_size=0)
    save_task = tasks[0]
    merge_task = save_task.deps[0]
    calc_tasks = merge_task.deps
    assert len(calc_tasks) == 1 + 1  # 1 hist region tasks, 1 for hist conf


def test_get_number_range_reads_histogram() -> None:
    histogram = NumberHistogram(NumberHistogramConfig((0.0, 1.0)))
    histogram.min_value = 0.25
    histogram.max_value = 0.75

    res = build_simple_position_score_resource({
        "statistics/histogram_score.json": histogram.serialize(),
    })

    score = build_score_from_resource(res)
    score.open()

    assert score.get_number_range("score") == (0.25, 0.75)


def test_get_number_range_returns_none_for_null_histogram() -> None:
    null_hist = NullHistogram(NullHistogramConfig("disabled"))
    res = build_simple_position_score_resource({
        "statistics/histogram_score.json": null_hist.serialize(),
    })

    score = build_score_from_resource(res)
    score.open()

    assert score.get_number_range("score") is None


def test_get_number_range_unknown_score_raises() -> None:
    score = build_score_from_resource(build_simple_position_score_resource())
    score.open()

    with pytest.raises(ValueError, match="unknown score missing"):
        score.get_number_range("missing")


def test_get_histogram_filename_prefers_yaml_from_manifest() -> None:
    manifest_content = textwrap.dedent(
        """
        - name: genomic_resource.yaml
          size: 0
          md5: ""
        - name: statistics/histogram_score.yaml
          size: 0
          md5: ""
        """)
    yaml_hist = textwrap.dedent(
        """
        config:
          type: null
          reason: disabled
        """)
    res = build_simple_position_score_resource(
        {
            ".MANIFEST": manifest_content,
            "statistics/histogram_score.yaml": yaml_hist,
        },
    )
    score = build_score_from_resource(res)

    assert score.get_histogram_filename("score") == \
        "statistics/histogram_score.yaml"


def test_get_histogram_image_filename_and_url() -> None:
    score = build_score_from_resource(build_simple_position_score_resource())

    assert score.get_histogram_image_filename("score") == \
        "statistics/histogram_score.png"
    url = score.get_histogram_image_url("score")
    assert url is not None
    assert url.endswith("/statistics/histogram_score.png")


def test_fetch_region_lines_requires_open() -> None:
    score = build_score_from_resource(build_simple_position_score_resource())

    region_iter = score._fetch_region_lines("1", 10, 10)
    with pytest.raises(ValueError, match="is not open"):
        next(region_iter)


def test_fetch_region_lines_checks_available_chromosomes() -> None:
    score = build_score_from_resource(build_simple_position_score_resource())
    score.open()

    with pytest.raises(ValueError, match="not among the available"):
        next(score._fetch_region_lines("2", 10, 10))


def test_line_to_begin_end_validates_order() -> None:
    bad_line = ScoreLine(
        Line(("1", "20", "10")),
        {},
    )

    with pytest.raises(OSError, match="has a regions"):
        GenomicScore._line_to_begin_end(bad_line)


def test_default_annotation_requires_list() -> None:
    res = build_inmemory_test_resource({
        GR_CONF_FILE_NAME: textwrap.dedent("""
            type: position_score
            table:
                filename: data.mem
            scores:
                - id: score
                  type: float
                  name: score
            default_annotation:
                attributes:
                    - score
        """),
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos_end score
            1     10        10      0.1
        """),
    })
    score = build_score_from_resource(res)
    score.open()

    with pytest.raises(TypeError, match="default_annotation"):
        score.get_default_annotation_attributes()
