# import pytest

# import os

# from dae.tools.generate_common_report import main


# @pytest.fixture(scope="function")
# def use_common_reports(wdae_gpf_instance):
#     all_configs = wdae_gpf_instance.get_all_common_report_configs()
#     temp_files = [config.file_path for config in all_configs]

#     for temp_file in temp_files:
#         if os.path.exists(temp_file):
#             os.remove(temp_file)

#     args = ["--studies", "Study1,study4"]

#     main(args, wdae_gpf_instance)

#     yield

#     for temp_file in temp_files:
#         if os.path.exists(temp_file):
#             os.remove(temp_file)
