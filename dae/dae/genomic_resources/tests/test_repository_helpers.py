# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.genomic_resources.repository import parse_gr_id_version_token
from dae.genomic_resources.repository import \
    is_version_constraint_satisfied


def test_parse_gr_id_version_token() -> None:
    with pytest.raises(ValueError):
        parse_gr_id_version_token("aaa(3.")

    with pytest.raises(ValueError):
        parse_gr_id_version_token("aaa(3.a)")
    with pytest.raises(ValueError):
        parse_gr_id_version_token("(3.2)")
    with pytest.raises(ValueError):
        parse_gr_id_version_token("aa*(3.0)")
    with pytest.raises(ValueError):
        parse_gr_id_version_token("aa(0)")
    with pytest.raises(ValueError):
        parse_gr_id_version_token("aa(0.2.3)")

    assert parse_gr_id_version_token("aa") == ("aa", (0,))
    assert parse_gr_id_version_token("aa(2)") == ("aa", (2,))
    assert parse_gr_id_version_token("aa(2.2.4.1)") == ("aa", (2, 2, 4, 1))


def test_is_version_constraint_satisfied() -> None:
    assert is_version_constraint_satisfied(None, (0,))
    assert is_version_constraint_satisfied(None, (1, 2))

    assert is_version_constraint_satisfied("1.2", (1, 2))
    assert is_version_constraint_satisfied("1.2", (1, 3))
    assert is_version_constraint_satisfied("1.2", (1, 2, 1))
    assert not is_version_constraint_satisfied("1.2", (1, 1))

    assert is_version_constraint_satisfied(">=1.2", (1, 2))
    assert is_version_constraint_satisfied(">=1.2", (1, 3))
    assert is_version_constraint_satisfied(">=1.2", (1, 2, 1))
    assert not is_version_constraint_satisfied(">=1.2", (1, 1))

    assert is_version_constraint_satisfied("=1.2", (1, 2))
    assert not is_version_constraint_satisfied("=1.2", (1, 3))
    assert not is_version_constraint_satisfied("=1.2", (1, 2, 1))
    assert not is_version_constraint_satisfied("=1.2", (1, 1))


# def test_find_genomic_resources_helper(caplog):
#     from dae.genomic_resources.repository import
#       find_genomic_resources_helper
#     from dae.genomic_resources.repository import GR_CONF_FILE_NAME

#     caplog.set_level(logging.WARNING)
#     assert set(["one:(0,)",
#                 "two:(0,)", "two:(1, 0, 1)",
#                 "group/three2.0:(0,)", "group/three2.0:(1, 0)",
#                 "group/three2.0:(1, 0, 1)",
#                 "group/three3.1:(0,)", "group/three3.1:(1, 0, 1)",
#                 "group/four:(0,)"]) == \
#         {f"{res_id}:{res_ver}"
#           for res_id, res_ver in find_genomic_resources_helper(
#             {
#                 "one":        {GR_CONF_FILE_NAME: ""},
#                 "bla": "",
#                 "two":        {GR_CONF_FILE_NAME: ""},
#                 "two(1.0.1)": {GR_CONF_FILE_NAME: ""},
#                 "group": {
#                     "three2.0":        {GR_CONF_FILE_NAME: ""},
#                     "three2.0(1.0)":   {GR_CONF_FILE_NAME: ""},
#                     "three2.0(1.0.1)": {GR_CONF_FILE_NAME: ""},
#                     "three3.1":        {GR_CONF_FILE_NAME: ""},
#                     "three3.1(1.0.1)": {GR_CONF_FILE_NAME: ""},
#                     "four":            {GR_CONF_FILE_NAME: ""},
#                     "tralala&":        {},
#                     "bala": {"bala": {}}
#                 },
#                 "tra": {"la": {"la": {}}}
#             })
#          }
#     assert set(caplog.record_tuples) == \
#         {("dae.genomic_resources.repository", logging.WARNING, msg)
#          for msg in [
#             "file <bla> is not used.",
#             "directory <group/tralala&> has a name <tralala&> that is not a "
#             "valid Genomic Resource Id Token.",
#             "directory <tra> contains no resources.",
#             "directory <group/bala> contains no resources."
#         ]}


# def test_one_resource_repo():
#     from dae.genomic_resources.repository import
#           find_genomic_resources_helper
#     from dae.genomic_resources.repository import GR_CONF_FILE_NAME

#     assert set(["[0]"]) == \
#         {f"{rId}[{".".join(map(str,rVersion))}]"
#             for rId, rVersion in find_genomic_resources_helper(
#                 {GR_CONF_FILE_NAME: ""})}
