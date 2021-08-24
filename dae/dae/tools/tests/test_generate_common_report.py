from dae.tools.generate_common_report import main


def test_generate_common_report(gpf_instance_2013):
    main(["--studies", " "], gpf_instance_2013)
    main(["--show-studies"], gpf_instance_2013)
