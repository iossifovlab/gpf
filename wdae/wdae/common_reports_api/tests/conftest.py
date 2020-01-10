import pytest

import os

# from dae.gpf_instance.gpf_instance import GPFInstance
# from gpf_instance.gpf_instance import reload_datasets
# from dae_conftests.dae_conftests import get_global_dae_fixtures_dir


@pytest.fixture(scope='function')
def common_report_facade(wdae_gpf_instance):
    return wdae_gpf_instance._common_report_facade


@pytest.fixture(scope='function')
def use_common_reports(common_report_facade):
    all_configs = common_report_facade.get_all_common_report_configs()
    temp_files = [config.file_path for config in all_configs]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    common_report_facade.generate_common_report('Study1')
    common_report_facade.generate_common_report('study4')

    yield

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

