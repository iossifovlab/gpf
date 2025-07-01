# pylint: disable=W0621,C0114,C0116,W0212,W0613
from gpf_instance.gpf_instance import WGPFInstance
from studies.study_wrapper import WDAEStudy, WDAEStudyGroup

from federation.remote_study_wrapper import (
    RemoteWDAEStudy,
    RemoteWDAEStudyGroup,
)


def test_get_available_data_ids(t4c8_instance: WGPFInstance) -> None:
    assert t4c8_instance.get_available_data_ids() == [
        "t4c8_dataset", "t4c8_study_1", "TEST_REMOTE_t4c8_dataset",
        "TEST_REMOTE_t4c8_study_1", "t4c8_study_2", "TEST_REMOTE_t4c8_study_4",
        "study_1_pheno", "TEST_REMOTE_t4c8_study_2",
        "TEST_REMOTE_study_1_pheno", "t4c8_study_4",
    ]


def test_get_wdae_wrapper(t4c8_instance: WGPFInstance) -> None:
    for study_id in [
        "t4c8_dataset",
        "t4c8_study_1",
        "t4c8_study_2",
        "study_1_pheno",
        "t4c8_study_4",
    ]:
        assert isinstance(
            t4c8_instance.get_wdae_wrapper(study_id),
            (WDAEStudyGroup, WDAEStudy),
        ) is True

    for study_id in [
        "TEST_REMOTE_t4c8_dataset",
        "TEST_REMOTE_t4c8_study_1",
        "TEST_REMOTE_t4c8_study_4",
        "TEST_REMOTE_t4c8_study_2",
        "TEST_REMOTE_study_1_pheno",
    ]:
        assert isinstance(
            t4c8_instance.get_wdae_wrapper(study_id),
            (RemoteWDAEStudy, RemoteWDAEStudyGroup),
        ) is True
