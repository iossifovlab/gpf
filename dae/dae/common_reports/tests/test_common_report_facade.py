import pytest

# pytestmark = pytest.mark.usefixtures("remove_common_reports")


def test_get_all_common_report_ids(common_report_facade):
    assert sorted(common_report_facade.get_all_common_report_ids()) == sorted(
        ["Study1", "Study3", "Study4", "Dataset1"]
    )
    assert len(common_report_facade._common_report_config_cache) == 4


def test_get_all_common_report_configs(common_report_facade):
    assert len(common_report_facade.get_all_common_report_configs()) == 4


@pytest.mark.parametrize(
    "study_ids,expected_count,missing",
    [
        # (["Study1"], 1, ["Study4, Dataset1"]),
        # (["Study4", "Dataset1"], 2, ["Study1"]),
        (["Study1", "Study3", "Study4", "Dataset1"], 4, []),
    ]
)
def test_generate_common_report(
        common_report_facade, study_ids, expected_count, missing):

    common_report_facade.generate_common_reports(study_ids)
    print(common_report_facade._common_report_cache.keys())
    assert len(common_report_facade._common_report_cache) == expected_count, \
        common_report_facade._common_report_cache.keys()

    for available_report in study_ids:
        assert common_report_facade\
            .get_common_report(available_report) is not None

    for missing_report in missing:
        assert common_report_facade.get_common_report(missing_report) is None


# def test_generate_all_common_reports(common_report_facade):
#     common_report_facade.generate_all_common_reports()
#     assert len(common_report_facade._common_report_cache) == 4


# def test_get_common_report(generate_common_reports, common_report_facade):
#     assert common_report_facade.get_common_report("Study1")
#     assert common_report_facade.get_common_report("Study10") is None


# def test_get_all_common_reports(
#           generate_common_reports, common_report_facade):
#     assert len(common_report_facade.get_all_common_reports()) == 4


# def test_get_common_report_config(common_report_facade):
#     assert common_report_facade.get_common_report_config("Dataset1")
#     assert common_report_facade.get_common_report_config("Dataset10") is None
