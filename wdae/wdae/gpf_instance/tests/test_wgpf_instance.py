# pylint: disable=W0621,C0114,C0116,W0212,W0613
from box import Box
from studies.study_wrapper import StudyWrapper

from dae.common_reports.common_report import CommonReport
from dae.studies.study import GenotypeDataStudy


def test_make_wdae_wrapper(wgpf_instance_fixture):
    wrapper = wgpf_instance_fixture.make_wdae_wrapper("quads_f1")
    assert isinstance(wrapper, StudyWrapper)


def test_get_wdae_wrapper(wgpf_instance_fixture):
    wrapper = wgpf_instance_fixture.get_wdae_wrapper("quads_f1")
    assert isinstance(wrapper, StudyWrapper)


def test_get_wdae_wrapper_nonexistant(wgpf_instance_fixture):
    wrapper = wgpf_instance_fixture.get_wdae_wrapper("a;kdljgsl;dhj")
    assert wrapper is None


def test_get_genotype_data_ids(wgpf_instance_fixture):
    assert len(wgpf_instance_fixture.get_genotype_data_ids()) == 38


def test_get_genotype_data(wgpf_instance_fixture):
    data_study = wgpf_instance_fixture.get_genotype_data("quads_f1")
    assert isinstance(data_study, GenotypeDataStudy)


def test_get_genotype_data_nonexistant(wgpf_instance_fixture):
    data_study = wgpf_instance_fixture.get_genotype_data("adjkl;gsflah")
    assert data_study is None


def test_get_genotype_data_config(wgpf_instance_fixture):
    data_config = wgpf_instance_fixture.get_genotype_data_config("quads_f1")
    assert isinstance(data_config, Box)


def test_get_genotype_data_config_nonexistant(wgpf_instance_fixture):
    data_config = wgpf_instance_fixture.get_genotype_data_config("asjglkshj")
    assert data_config is None


def test_get_common_report(wgpf_instance_fixture, use_common_reports):
    common_report = wgpf_instance_fixture.get_common_report("Study1")
    assert isinstance(common_report, CommonReport)


def test_get_common_report_nonexistant(wgpf_instance_fixture):
    common_report = wgpf_instance_fixture.get_common_report("aklghs")
    assert common_report is None
