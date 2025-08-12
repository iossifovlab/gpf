

from dae.common_reports.common_report import CommonReport
from gpf_instance.gpf_instance import WGPFInstance

from common_reports_api.views import create_common_reports_helper


def test_get_common_report(
    t4c8_wgpf_instance: WGPFInstance,
) -> None:
    """Test getting a common report from common report helper."""
    study = t4c8_wgpf_instance.get_wdae_wrapper("t4c8_study_1")
    assert study is not None
    common_reports_helper = create_common_reports_helper(
        t4c8_wgpf_instance,
        study,
    )
    common_report = common_reports_helper.get_common_report()
    assert isinstance(common_report, CommonReport)
