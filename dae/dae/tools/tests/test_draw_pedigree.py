# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

from dae.tools.draw_pedigree import main


def test_draw_pedigree_simple(tmp_path, fixture_dirname):
    input_file = os.path.join(fixture_dirname("backends"), "trios2.ped")
    output_file = str(tmp_path / "output.pdf")
    assert os.path.exists(input_file)

    argv = [
        input_file,
        "-o", output_file
    ]

    main(argv)

    assert os.path.exists(output_file)
