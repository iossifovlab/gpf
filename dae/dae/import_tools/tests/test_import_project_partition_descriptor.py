# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

from dae.import_tools.import_tools import ImportProject
from dae.testing import foobar_gpf, setup_directories


def test_import_project_parse_no_region_bins(tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path / "import_project.yaml", textwrap.dedent("""
            id: test_import

            input:
              pedigree:
                file: pedigree.ped

              denovo:
                files:
                  - single_chromosome_variants.tsv

            partition_description:
              frequency_bin:
                rare_boundary: 5

            destination:
              storage_type: schema2
        """),
    )

    config_fn = tmp_path / "import_project.yaml"
    project = ImportProject.build_from_file(config_fn)
    assert project is not None

    part_desc = project.get_partition_descriptor()
    assert part_desc is not None

    assert not part_desc.has_region_bins()
    assert not part_desc.has_family_bins()
    assert not part_desc.has_coding_bins()
    assert part_desc.has_frequency_bins()


def test_parse_region_bins_without_len(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "import_project.yaml", textwrap.dedent("""
            id: test_import

            input:
              pedigree:
                file: pedigree.ped

              denovo:
                files:
                  - single_chromosome_variants.tsv

            partition_description:
              region_bin:
                chromosomes: [foo, bar]

            destination:
              storage_type: schema2
        """),
    )

    gpf = foobar_gpf(tmp_path / "foobar")

    config_fn = tmp_path / "import_project.yaml"
    project = ImportProject.build_from_file(config_fn, gpf_instance=gpf)
    assert project is not None

    part_desc = project.get_partition_descriptor()
    assert part_desc is not None

    assert part_desc.has_region_bins()
    assert not part_desc.has_family_bins()
    assert not part_desc.has_coding_bins()
    assert not part_desc.has_frequency_bins()
