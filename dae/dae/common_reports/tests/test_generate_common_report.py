# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.common_reports.generate_common_report import main
from dae.gpf_instance import GPFInstance


def test_generate_common_report(gpf_instance_2013: GPFInstance) -> None:
    main(["--studies", " "], gpf_instance_2013)
    main(["--show-studies"], gpf_instance_2013)
