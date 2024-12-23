# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.common_reports.generate_common_report import main
from dae.gpf_instance import GPFInstance


def test_generate_common_report(t4c8_instance: GPFInstance) -> None:
    main(["--studies", " "], t4c8_instance)
    main(["--show-studies"], t4c8_instance)
