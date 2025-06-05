# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib

from dae.tools.draw_pedigree import main


def test_draw_pedigree_simple(
    t4c8_study_1_ped: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:

    input_file = str(t4c8_study_1_ped)
    output_file = str(tmp_path / "output.pdf")
    assert os.path.exists(input_file)

    argv = [
        input_file,
        "-o", output_file,
    ]

    main(argv)

    assert os.path.exists(output_file)
