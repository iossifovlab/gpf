# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.annotation.annotate_columns import build_record_to_annotatable
from dae.annotation.annotatable import Position, VCFAllele, Region
from dae.genomic_resources.test_tools import convert_to_tab_separated
from dae.annotation.annotate_columns import cli


@pytest.mark.parametrize(
    "record,expected", [
        ({"chrom": "chr1", "pos": "3"},
         Position("chr1", 3)),

        ({"chrom": "chr1", "pos": "4", "ref": "C", "alt": "CT"},
         VCFAllele("chr1", 4, "C", "CT")),

        ({"vcf_like": "chr1:4:C:CT"},
         VCFAllele("chr1", 4, "C", "CT")),

        ({"chrom": "chr1", "pos_beg": "4", "pos_end": "30"},
         Region("chr1", 4, 30)),
    ]
)
def test_default_columsn(record, expected):
    annotatable = build_record_to_annotatable(
        {}, set(record.keys())).build(record)
    assert str(annotatable) == str(expected)


@pytest.mark.parametrize(
    "parameters,record,expected", [

        ({"col_chrom": "chromosome", "col_pos": "position"},
         {"chromosome": "chr1", "position": "4", "ref": "C", "alt": "CT"},
         VCFAllele("chr1", 4, "C", "CT")),
    ]
)
def test_renamed_columsn(parameters, record, expected):
    annotatable = build_record_to_annotatable(
        parameters, set(record.keys())).build(record)
    assert str(annotatable) == str(expected)


def test_build_record_to_annotable_failures():
    with pytest.raises(Exception):
        build_record_to_annotatable({}, set([]))

    with pytest.raises(Exception):
        build_record_to_annotatable({"gosho": "pesho"}, set([]))


def setup_dir(directory, files):
    """Set up a directory with list of (file name, file content).

    TODO: There must be a pytest tool like that.
          If not, we should moved it to a more general location.
          Also, it should be extended to recursivelly build directories.
    """
    for file_name, file_content in files.items():
        with open(directory / file_name, "wt", encoding="utf8") as infile:
            infile.write(file_content)


def get_file_content_as_string(file):
    with open(file, "rt", encoding="utf8") as infile:
        return "".join(infile.readlines())


def test_basic_setup(tmp_path):
    in_content = convert_to_tab_separated("""
            chrom   pos
            chr1    23
            chr1    24
        """)
    out_expected_content = convert_to_tab_separated("""
            chrom   pos score
            chr1    23  0.01
            chr1    24  0.2
        """)

    setup_dir(tmp_path, {
        "in.txt": in_content,
        "annotation.yaml": """
            - position_score: one
            """,
        "grr.yaml": """
            id: mm
            type: embedded
            content:
                one:
                    genomic_resource.yaml: |
                        type: position_score
                        table:
                            filename: data.mem
                        scores:
                        - id: score
                          type: float
                          desc: |
                                The phastCons computed over the tree of 100
                                verterbarte species
                          name: s1
                    data.mem: |
                        chrom  pos_begin  s1
                        chr1   23         0.01
                        chr1   24         0.2

            """
    })
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    annotation_file = tmp_path / "annotation.yaml"
    grr_file = tmp_path / "grr.yaml"

    cli([
        str(a) for a in [
            in_file, annotation_file, out_file, "-grr", grr_file
        ]
    ])
    out_file_content = get_file_content_as_string(out_file)
    print(out_file_content)
    assert out_file_content == out_expected_content
