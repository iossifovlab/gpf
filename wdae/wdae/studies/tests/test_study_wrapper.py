# pylint: disable=W0621,C0114,C0116,W0212,W0613

from gpf_instance.gpf_instance import WGPFInstance

from dae.studies.study import GenotypeData


def test_t4c8_study_1(t4c8_study_1: GenotypeData) -> None:
    assert t4c8_study_1 is not None


def test_t4c8_study_2(t4c8_study_2: GenotypeData) -> None:
    assert t4c8_study_2 is not None


def test_t4c8_dataset(t4c8_dataset: GenotypeData) -> None:
    assert t4c8_dataset is not None


def test_is_group_study(t4c8_wgpf_instance: WGPFInstance) -> None:
    assert t4c8_wgpf_instance is not None

    wrapper = t4c8_wgpf_instance.get_wdae_wrapper("t4c8_study_1")
    assert wrapper is not None
    assert wrapper.is_group is False


def test_is_group_dataset(t4c8_wgpf_instance: WGPFInstance) -> None:
    wrapper = t4c8_wgpf_instance.get_wdae_wrapper("t4c8_dataset")
    assert wrapper is not None
    assert wrapper.is_group is True
