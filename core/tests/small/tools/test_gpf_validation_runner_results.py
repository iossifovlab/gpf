# pylint: disable=C0114,C0116
import pathlib
import textwrap
from typing import Any

import pytest

from gpf.tools import gpf_validation_runner

EXPECTATION = {
    "file": "expectations/study1.yaml",
    "study": "study1",
    "target": "genotype_browser",
}


def _result(
    status: gpf_validation_runner.TestStatus,
    params: dict[str, Any] | None = None,
    message: str | None = None,
) -> gpf_validation_runner.TestResult:
    result = gpf_validation_runner.TestResult(
        expectation=EXPECTATION,
        case={"name": "case one"},
        test_for="count",
        params={} if params is None else params,
    )
    result.status = status
    result.message = message
    return result


@pytest.mark.parametrize(
    "missing", ["case", "expectation", "params", "test_for"])
def test_to_xml_element_missing_field_raises(missing: str) -> None:
    result = _result(gpf_validation_runner.TestStatus.PASSED)
    setattr(result, missing, None)

    with pytest.raises(AssertionError):
        result.to_xml_element()


def test_to_xml_element_sets_the_attributes() -> None:
    result = _result(
        gpf_validation_runner.TestStatus.PASSED,
        params={"genes": ["A", 1], "limit": 5, "flag": None})
    result.time = 1.5

    element = result.to_xml_element()

    name = "Case case one: count|genes[A,1]|limit[5]|flag[None]"
    assert element.tag == "testcase"
    assert element.attrib == {
        "name": name,
        "time": "1.5",
        "filename": "expectations/study1.yaml",
        "classname": f"study1:genotype_browser:{name}",
    }


def test_to_xml_element_without_time_writes_none() -> None:
    result = _result(gpf_validation_runner.TestStatus.PASSED)

    element = result.to_xml_element()

    assert element.get("time") == "None"


@pytest.mark.parametrize(
    "status",
    [
        gpf_validation_runner.TestStatus.PASSED,
        gpf_validation_runner.TestStatus.NOTSET,
    ],
)
def test_to_xml_element_passed_and_notset_add_no_child(
    status: gpf_validation_runner.TestStatus,
) -> None:
    result = _result(status, message="ignored")

    element = result.to_xml_element()

    assert len(element) == 0


@pytest.mark.parametrize(
    "status, tag",
    [
        (gpf_validation_runner.TestStatus.FAIL, "failure"),
        (gpf_validation_runner.TestStatus.ERROR, "error"),
    ],
)
def test_to_xml_element_fail_and_error_add_a_child(
    status: gpf_validation_runner.TestStatus, tag: str,
) -> None:
    result = _result(status, message="went wrong")

    element = result.to_xml_element()

    children = list(element)
    assert len(children) == 1
    assert children[0].tag == tag
    assert children[0].attrib == {"message": "went wrong"}


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.write_text(textwrap.dedent(content))
    return path


def test_collect_expectations_no_match_yields_nothing(
    tmp_path: pathlib.Path,
) -> None:
    result = gpf_validation_runner.MainRunner.collect_expectations(
        str(tmp_path / "*.yaml"))

    assert len(list(result)) == 0


def test_collect_expectations_adds_file_and_id(
    tmp_path: pathlib.Path,
) -> None:
    path = _write(tmp_path / "e.yaml", """\
        - study: s1
          cases:
            - name: "A-b <=(5%)/x+y's"
            - name: Plain Name
        - study: s2
          cases:
            - name: other
        """)

    result = list(gpf_validation_runner.MainRunner.collect_expectations(
        str(tmp_path / "*.yaml")))

    assert result == [
        {
            "study": "s1",
            "file": str(path),
            "cases": [
                {"name": "A-b <=(5%)/x+y's", "id": "a_b_5_x_p_ys"},
                {"name": "Plain Name", "id": "plain_name"},
            ],
        },
        {
            "study": "s2",
            "file": str(path),
            "cases": [{"name": "other", "id": "other"}],
        },
    ]


def test_collect_expectations_reads_every_matching_file(
    tmp_path: pathlib.Path,
) -> None:
    _write(tmp_path / "a.yaml", "- {study: s1, cases: []}\n")
    _write(tmp_path / "b.yaml", "- {study: s2, cases: []}\n")

    result = gpf_validation_runner.MainRunner.collect_expectations(
        str(tmp_path / "*.yaml"))

    assert sorted(e["study"] for e in result) == ["s1", "s2"]


def test_collect_expectations_case_without_name_raises_on_read(
    tmp_path: pathlib.Path,
) -> None:
    _write(tmp_path / "e.yaml", "- {study: s1, cases: [{params: null}]}\n")
    result = gpf_validation_runner.MainRunner.collect_expectations(
        str(tmp_path / "*.yaml"))

    with pytest.raises(AssertionError):
        next(result)


def test_collect_expectations_duplicate_id_raises_on_read(
    tmp_path: pathlib.Path,
) -> None:
    _write(tmp_path / "e.yaml", """\
        - study: s1
          cases:
            - name: A B
            - name: a-b
        """)
    result = gpf_validation_runner.MainRunner.collect_expectations(
        str(tmp_path / "*.yaml"))

    with pytest.raises(AssertionError):
        next(result)


def test_collect_expectations_yields_before_a_later_bad_expectation(
    tmp_path: pathlib.Path,
) -> None:
    _write(tmp_path / "e.yaml", """\
        - study: good
          cases:
            - name: one
        - study: bad
          cases:
            - name: x
            - name: X
        """)
    result = gpf_validation_runner.MainRunner.collect_expectations(
        str(tmp_path / "*.yaml"))

    assert next(result)["study"] == "good"
    with pytest.raises(AssertionError):
        next(result)
