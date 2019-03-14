from tools.generate_common_report import main


def test_generate_common_report():
    main(argv=['--studies', ' '])
    main(argv=['--show-studies'])
