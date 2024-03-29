# pylint: disable=W0621,C0114,C0116,W0212,W0613
from gpf_instance.gpf_instance import WGPFInstance


def test_is_group_study(wdae_gpf_instance: WGPFInstance) -> None:
    wrapper = wdae_gpf_instance.get_wdae_wrapper("f1_study")
    assert wrapper is not None
    assert wrapper.is_group is False


def test_is_group_dataset(wdae_gpf_instance: WGPFInstance) -> None:
    wrapper = wdae_gpf_instance.get_wdae_wrapper("Dataset1")
    assert wrapper is not None
    assert wrapper.is_group is True
