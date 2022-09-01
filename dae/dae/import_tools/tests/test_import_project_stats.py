# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.import_tools.import_tools import ImportProject


def test_stats_simple():
    project = ImportProject({"input": {}}, ".")
    assert project is not None

    project.put_stats(("a", ), 1)
    project.put_stats(("b", "1"), 1)
    project.put_stats(("b", "2"), 2)

    assert project.get_stats(("a", )) == 1
    assert project.get_stats(("b", "1")) == 1
    assert project.get_stats(("b", "2")) == 2


def test_stats_put_bad():
    project = ImportProject({"input": {}}, ".")
    assert project is not None

    project.put_stats(("a", ), 1)
    with pytest.raises(ValueError):
        project.put_stats(("a", "1"), 1)


def test_stats_get():
    project = ImportProject({"input": {}}, ".")
    assert project is not None

    project.put_stats(("a", ), 1)
    project.put_stats(("b", "1"), 1)
    project.put_stats(("b", "2"), 2)

    assert project.get_stats(("b", "1")) == 1
    assert project.get_stats(("b", "3")) is None

    assert project.get_stats(("c",)) is None


def test_stats_get_bad():
    project = ImportProject({"input": {}}, ".")
    assert project is not None

    project.put_stats(("a", ), 1)

    with pytest.raises(ValueError):
        project.get_stats(("a", "1"))
