import common.config


def test_config_to_dict(configuration):
    result = common.config.to_dict(configuration)
    assert result is not None

    sections = list(result.keys())

    assert sections[0] == 'Step1'
    assert len(sections) == 5

    assert sections == ['Step1', 'Step2', 'Step3', 'Step4', 'Step5', ]
