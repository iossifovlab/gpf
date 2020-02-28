from dae.tools.generate_common_report import main


def test_generate_common_report(gpf_instance_2013):
    main(gpf_instance_2013, argv=["--studies", " "])
    main(gpf_instance_2013, argv=["--show-studies"])
