import pytest

import os
import shutil
from box import Box

# from dae.annotation.tools.file_io import IOManager, IOType
from dae.utils.fixtures import change_environment


def relative_to_this_test_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


# @pytest.fixture
# def vcf_variants_io(request):
#     def build(fixture_name, options=Box({})):
#         io_options = options.to_dict()
#         io_config = {
#             "infile": relative_to_this_test_folder(fixture_name),
#             "outfile": "-",
#         }
#         io_options.update(io_config)

#         io_options = Box(io_options, default_box=True, default_box_attr=None)
#         io_manager = IOManager(io_options, IOType.TSV, IOType.TSV)
#         return io_manager

#     return build


# @pytest.fixture(scope="module")
# def gene_info_cache_dir():
#     cache_dir = relative_to_this_test_folder("fixtures/geneInfo/cache")
#     assert not os.path.exists(
#         cache_dir
#     ), 'Cache dir "{}"already  exists..'.format(cache_dir)
#     os.makedirs(cache_dir)

#     new_envs = {
#         "DATA_STUDY_GROUPS_DENOVO_GENE_SETS_DIR": cache_dir,
#         "DAE_DB_DIR": relative_to_this_test_folder("fixtures"),
#     }

#     for val in change_environment(new_envs):
#         yield val

#     shutil.rmtree(cache_dir)
