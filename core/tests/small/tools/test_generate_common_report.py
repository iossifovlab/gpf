# pylint: disable=W0621,C0114,C0116,W0212,W0613
from gpf.gpf_instance import GPFInstance
from gpf.tools.generate_common_report import main


def test_generate_common_report(t4c8_instance: GPFInstance) -> None:
    main(["--studies", " "], gpf_instance=t4c8_instance)
    main(["--show-studies"], gpf_instance=t4c8_instance)
