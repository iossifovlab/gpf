from dae.genomic_resources.test_tools import convert_to_tab_separated
from dae.annotation_cli.annotate_columns import cli


def setup_dir(dir, files):
    '''
    TODO: There must be a pytest tool like that.
          If not, we should moved it to a more general location.
          Also, it should be extended to recursivelly build directories.
    '''
    for file_name, file_content in files.items():
        with open(dir / file_name, "wt") as F:
            F.write(file_content)


def get_file_content_as_string(file):
    with open(file, "rt") as F:
        return "".join(F.readlines())


def test_basic_setup(tmp_path):
    in_content = convert_to_tab_separated('''
            chrom   pos
            chr1    23
            chr1    24
        ''')
    out_expected_content = convert_to_tab_separated('''
            chrom   pos score
            chr1    23  0.01
            chr1    24  0.2
        ''')

    setup_dir(tmp_path, {
        "in.txt": in_content,
        "annotation.yaml": '''
            - position_score: one
            ''',
        "grr.yaml": '''
            id: mm
            type: embeded
            content:
                one:
                    genomic_resource.yaml: |
                        type: PositionScore
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

            '''
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
