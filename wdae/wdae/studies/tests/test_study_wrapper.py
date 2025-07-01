# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.studies.study import GenotypeData
from gpf_instance.gpf_instance import WGPFInstance

from studies.study_wrapper import WDAEStudy


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


def test_make_config(t4c8_dataset: GenotypeData) -> None:
    config = WDAEStudy.make_config(
        genotype_data=t4c8_dataset,
        phenotype_data=None,
    )
    assert isinstance(config, dict)
    assert config.get("id") == "t4c8_dataset"
    assert config.get("phenotype_data") is None


def test_genotype_data_config_immutability(
    t4c8_wgpf_instance: WGPFInstance,
    t4c8_dataset: GenotypeData,
) -> None:
    description = WDAEStudy.build_genotype_data_description(
        t4c8_wgpf_instance,
        t4c8_dataset,
        person_set_collection_configs=None,
    )
    assert description["common_report"]["file_path"] is None
    assert (
        "datasets/t4c8_dataset/common_report.json"
    ) in t4c8_dataset.config["common_report"]["file_path"]
