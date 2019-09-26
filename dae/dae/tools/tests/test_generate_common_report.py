from dae.tools.generate_common_report import main


def test_generate_common_report(gpf_instance):
    main(gpf_instance, argv=['--studies', ' '])
    main(gpf_instance, argv=['--show-studies'])
