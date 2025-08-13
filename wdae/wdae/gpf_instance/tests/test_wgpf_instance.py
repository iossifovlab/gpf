# pylint: disable=W0621,C0114,C0116,W0212,W0613
from box import Box
from dae.studies.study import GenotypeDataStudy
from studies.study_wrapper import WDAEStudy

from gpf_instance.gpf_instance import WGPFInstance


def test_make_wdae_wrapper(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    wrapper = t4c8_wgpf_instance.make_wdae_wrapper("t4c8_study_1")
    assert isinstance(wrapper, WDAEStudy)


def test_get_wdae_wrapper(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    wrapper = t4c8_wgpf_instance.get_wdae_wrapper("t4c8_study_1")
    assert isinstance(wrapper, WDAEStudy)


def test_get_wdae_wrapper_nonexistant(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    wrapper = t4c8_wgpf_instance.get_wdae_wrapper("a;kdljgsl;dhj")
    assert wrapper is None


def test_get_genotype_data_ids(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    assert len(t4c8_wgpf_instance.get_genotype_data_ids()) == 4


def test_get_genotype_data(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    data_study = t4c8_wgpf_instance.get_genotype_data("t4c8_study_1")
    assert isinstance(data_study, GenotypeDataStudy)


def test_get_genotype_data_nonexistant(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    data_study = t4c8_wgpf_instance.get_genotype_data("adjkl;gsflah")
    assert data_study is None


def test_get_genotype_data_config(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    data_config = t4c8_wgpf_instance.get_genotype_data_config("t4c8_study_1")
    assert isinstance(data_config, Box)


def test_get_genotype_data_config_nonexistant(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    data_config = t4c8_wgpf_instance.get_genotype_data_config("asjglkshj")
    assert data_config is None
