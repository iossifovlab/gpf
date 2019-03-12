from tools.generate_common_report import main


def test_generate_common_report():
    main(options=['--studies', ' '])
    main(options=['--show-studies'])
