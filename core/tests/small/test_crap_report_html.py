# pylint: disable=W0621,C0116
"""``scripts/crap_report_html.py`` renders the CRAP table of crapper."""
import importlib.util
import pathlib
import sys
import textwrap
from types import ModuleType

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "crap_report_html.py"

TABLE = textwrap.dedent("""\
    CRAP Report
    ===========
    Languages: python

    Function      Namespace                  CC    Cov%     CRAP
    ------------------------------------------------------------
    cli_vcf       gpf.effect_annotation.cli 10   0.0%    110.0
    parse_gtf     gpf.gene_models.parsers   24  97.4%     24.0
    __lt__        gpf.utils.Region<T>        3  50.0%      4.1
    """)


@pytest.fixture(scope="module")
def crap_report_html() -> ModuleType:
    if not SCRIPT.exists():
        pytest.fail(f"{SCRIPT} is missing; core/Dockerfile must copy it")
    spec = importlib.util.spec_from_file_location(
        "crap_report_html", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_page_title_names_gpf(
    crap_report_html: ModuleType,
) -> None:
    page = crap_report_html.render_html(
        crap_report_html.parse_crap_table(TABLE))

    assert "<title>CRAP report of gpf</title>" in page
    assert "<h1>CRAP report of gpf</h1>" in page
    assert "gain" not in page


def test_parse_reads_every_row_after_the_rule(
    crap_report_html: ModuleType,
) -> None:
    rows = crap_report_html.parse_crap_table(TABLE)

    assert [
        (row.function, row.complexity, row.coverage, row.crap)
        for row in rows
    ] == [
        ("cli_vcf", 10, 0.0, 110.0),
        ("parse_gtf", 24, 97.4, 24.0),
        ("__lt__", 3, 50.0, 4.1),
    ]


def test_parse_of_text_without_the_rule_is_empty(
    crap_report_html: ModuleType,
) -> None:
    assert crap_report_html.parse_crap_table("crapper: no files\n") == []


def test_page_has_the_summary_counts_and_one_row_per_function(
    crap_report_html: ModuleType,
) -> None:
    rows = crap_report_html.parse_crap_table(TABLE)

    page = crap_report_html.render_html(rows)

    assert "<li>Functions: 3</li>" in page
    assert "<li>CRAP &gt;= 30: 1</li>" in page
    assert "<li>CRAP &gt;= 10: 2</li>" in page
    assert "<li>Coverage 0%: 1</li>" in page
    assert page.count("<tr><td>") == 3
    assert (
        "<tr><td>cli_vcf</td><td>gpf.effect_annotation.cli</td>"
        '<td align="right">10</td><td align="right">0.0%</td>'
        '<td align="right">110.0</td></tr>') in page


def test_page_escapes_the_namespace(
    crap_report_html: ModuleType,
) -> None:
    page = crap_report_html.render_html(
        crap_report_html.parse_crap_table(TABLE))

    assert "gpf.utils.Region&lt;T&gt;" in page
    assert "Region<T>" not in page


def test_main_writes_a_no_rows_page_for_a_missing_table(
    crap_report_html: ModuleType, tmp_path: pathlib.Path,
) -> None:
    target = tmp_path / "crap.html"

    exit_code = crap_report_html.main(
        ["crap_report_html.py", str(tmp_path / "absent.txt"), str(target)])

    assert exit_code == 0
    assert "crapper wrote no rows." in target.read_text()
    assert "<table" not in target.read_text()


def churn_log(*commits: list[str]) -> str:
    """Render ``git log --name-status`` text, newest commit first."""
    return "".join(
        "@@commit:0123abc\n\n" + "".join(f"{line}\n" for line in commit)
        for commit in commits)


def test_churn_counts_an_edit_before_and_after_a_rename(
    crap_report_html: ModuleType,
) -> None:
    log = churn_log(
        ["M\tcore/gpf/new.py"],
        ["R100\tcore/gpf/old.py\tcore/gpf/new.py"],
        ["M\tcore/gpf/old.py"],
    )

    churn = crap_report_html.parse_churn_log(log)

    assert churn == {"core/gpf/new.py": 2}


def test_churn_follows_a_chain_of_renames(
    crap_report_html: ModuleType,
) -> None:
    log = churn_log(
        ["R100\tgpf_core/gpf/a.py\tcore/gpf/a.py"],
        ["M\tgpf_core/gpf/a.py"],
        ["R100\tgpf/gpf/a.py\tgpf_core/gpf/a.py"],
        ["R100\tdae/dae/a.py\tgpf/gpf/a.py"],
        ["M\tdae/dae/a.py"],
    )

    churn = crap_report_html.parse_churn_log(log)

    assert churn == {"core/gpf/a.py": 2}


def test_pure_rename_adds_zero_and_rename_with_edits_adds_one(
    crap_report_html: ModuleType,
) -> None:
    log = churn_log(
        ["R100\tcore/gpf/a_old.py\tcore/gpf/a.py",
         "R093\tcore/gpf/b_old.py\tcore/gpf/b.py"],
    )

    churn = crap_report_html.parse_churn_log(log)

    assert churn.get("core/gpf/a.py", 0) == 0
    assert churn["core/gpf/b.py"] == 1


def test_commit_counts_once_for_a_file_with_two_old_paths(
    crap_report_html: ModuleType,
) -> None:
    log = churn_log(
        ["R100\tcore/gpf/b.py\tcore/gpf/a.py"],
        ["D\tcore/gpf/a.py"],
        ["M\tcore/gpf/a.py", "M\tcore/gpf/b.py"],
    )

    churn = crap_report_html.parse_churn_log(log)

    assert churn == {"core/gpf/a.py": 2}


def test_commit_of_100_files_adds_zero_but_keeps_its_renames(
    crap_report_html: ModuleType,
) -> None:
    big_rename = [
        f"R087\tgpf_core/gpf/m{i}.py\tcore/gpf/m{i}.py"
        for i in range(99)
    ] + ["R087\tgpf_core/gpf/a.py\tcore/gpf/a.py"]
    log = churn_log(
        big_rename,
        ["M\tgpf_core/gpf/a.py"],
    )

    churn = crap_report_html.parse_churn_log(log)

    assert churn == {"core/gpf/a.py": 1}


def test_commit_of_99_files_counts(
    crap_report_html: ModuleType,
) -> None:
    log = churn_log([f"M\tcore/gpf/m{i}.py" for i in range(99)])

    churn = crap_report_html.parse_churn_log(log)

    assert len(churn) == 99
    assert set(churn.values()) == {1}


@pytest.fixture
def source_root(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "core"
    (root / "gpf" / "binning").mkdir(parents=True)
    (root / "gpf" / "__init__.py").write_text("")
    (root / "gpf" / "binning" / "__init__.py").write_text("")
    (root / "gpf" / "binning" / "tracks.py").write_text("")
    return root


@pytest.mark.parametrize(("namespace", "expected"), [
    ("gpf.binning.tracks", "core/gpf/binning/tracks.py"),
    ("gpf.binning", "core/gpf/binning/__init__.py"),
    ("gpf.binning.tracks.BoundTrackKind", "core/gpf/binning/tracks.py"),
    ("gpf.binning.tracks.Region<T>", "core/gpf/binning/tracks.py"),
])
def test_namespace_maps_to_the_file_of_its_longest_module_prefix(
    crap_report_html: ModuleType, source_root: pathlib.Path,
    namespace: str, expected: str,
) -> None:
    assert crap_report_html.namespace_file(namespace, source_root) == expected


def test_namespace_without_a_file_maps_to_none(
    crap_report_html: ModuleType, source_root: pathlib.Path,
) -> None:
    assert crap_report_html.namespace_file("other.pkg", source_root) is None


def test_namespace_key_starts_with_the_name_of_the_root(
    crap_report_html: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / "web_api"
    (root / "gpf_web").mkdir(parents=True)
    (root / "gpf_web" / "views.py").write_text("")

    assert crap_report_html.namespace_file(
        "gpf_web.views.Index", root) == "web_api/gpf_web/views.py"


def test_hotspot_of_a_namespace_without_a_file_has_zero_commits(
    crap_report_html: ModuleType, source_root: pathlib.Path,
) -> None:
    rows = [crap_report_html.CrapRow("f", "other.pkg", 1, 0.0, 5.0)]

    hotspots = crap_report_html.rank_hotspots(
        rows, {"core/gpf/binning/tracks.py": 3}, source_root)

    assert [(hotspot.commits, hotspot.score) for hotspot in hotspots] == [
        (0, 0.0)]


@pytest.fixture
def table_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """A source root with the files of the namespaces of ``TABLE``."""
    root = tmp_path / "core"
    for path in ("gpf/effect_annotation/cli.py",
                 "gpf/gene_models/parsers.py", "gpf/utils.py"):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text("")
    return root


def run_main(
    crap_report_html: ModuleType, tmp_path: pathlib.Path,
    *churn_args: str,
) -> tuple[int, str]:
    source = tmp_path / "crap.txt"
    source.write_text(TABLE)
    target = tmp_path / "crap.html"
    exit_code = crap_report_html.main(
        ["crap_report_html.py", str(source), str(target), *churn_args])
    return exit_code, target.read_text()


def test_page_ranks_hotspots_by_crap_times_churn(
    crap_report_html: ModuleType, tmp_path: pathlib.Path,
    table_root: pathlib.Path,
) -> None:
    log = tmp_path / "churn.txt"
    log.write_text(churn_log(
        *[["M\tcore/gpf/gene_models/parsers.py"]] * 10,
        ["M\tcore/gpf/effect_annotation/cli.py"],
    ))

    exit_code, page = run_main(
        crap_report_html, tmp_path, str(log), str(table_root))

    assert exit_code == 0
    hotspots = page[page.index("<h2>Hotspots</h2>"):]
    assert (
        "<th>Function</th><th>Namespace</th><th>CRAP</th>"
        "<th>Commits in 12 months</th><th>Hotspot score</th>") in hotspots
    assert [
        line.split("</td>")[0].removeprefix("<tr><td>")
        for line in hotspots.splitlines() if line.startswith("<tr><td>")
    ] == ["parse_gtf", "cli_vcf", "__lt__"]
    assert (
        "<tr><td>parse_gtf</td><td>gpf.gene_models.parsers</td>"
        '<td align="right">24.0</td><td align="right">10</td>'
        '<td align="right">240.0</td></tr>') in hotspots
    assert page.index("<h2>Hotspots</h2>") > page.index("<td>cli_vcf</td>")


def test_hotspot_table_holds_at_most_50_rows(
    crap_report_html: ModuleType, table_root: pathlib.Path,
) -> None:
    rows = [
        crap_report_html.CrapRow(
            f"f{i}", "gpf.utils", 1, 0.0, float(i))
        for i in range(60)]

    hotspots = crap_report_html.rank_hotspots(
        rows, {"core/gpf/utils.py": 2}, table_root)

    assert len(hotspots) == 50
    assert hotspots[0].row.function == "f59"
    assert hotspots[0].score == 118.0
    assert hotspots[-1].row.function == "f10"


MISSING_CHURN = (
    "<p>The churn count is missing, so the page has no hotspot table.</p>")


def test_page_without_the_churn_argument_says_the_count_is_missing(
    crap_report_html: ModuleType, tmp_path: pathlib.Path,
) -> None:
    exit_code, page = run_main(crap_report_html, tmp_path)

    assert exit_code == 0
    assert "<td>cli_vcf</td>" in page
    assert MISSING_CHURN in page


def test_page_with_a_missing_churn_file_says_the_count_is_missing(
    crap_report_html: ModuleType, tmp_path: pathlib.Path,
    table_root: pathlib.Path,
) -> None:
    exit_code, page = run_main(
        crap_report_html, tmp_path,
        str(tmp_path / "absent.txt"), str(table_root))

    assert exit_code == 0
    assert "<td>cli_vcf</td>" in page
    assert MISSING_CHURN in page


def test_page_with_an_empty_churn_file_says_the_count_is_missing(
    crap_report_html: ModuleType, tmp_path: pathlib.Path,
    table_root: pathlib.Path,
) -> None:
    log = tmp_path / "churn.txt"
    log.write_text("")

    exit_code, page = run_main(
        crap_report_html, tmp_path, str(log), str(table_root))

    assert exit_code == 0
    assert "<td>cli_vcf</td>" in page
    assert MISSING_CHURN in page
