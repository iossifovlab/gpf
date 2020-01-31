from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.annotation.tools.cleanup_annotator import CleanupAnnotator
from dae.annotation.tools.annotator_config import AnnotationConfigParser

expected_cleanup_output = '''location
4:4372372973
10:4372372973
X:4372
Y:4372
'''


def test_cleanup_annotator(capsys, variants_io, genomes_db_2013):
    section_config = AnnotationConfigParser.parse_section(
        GPFConfigParser._dict_to_namedtuple({
            'options': {},
            'columns': {
                'cleanup': 'id, variant',
            },
            'annotator': 'cleanup_annotator.CleanupAnnotator',
            'virtual_columns': [],
        }),
        genomes_db_2013
    )

    with variants_io('fixtures/input.tsv') as io_manager:
        annotator = CleanupAnnotator(section_config)
        assert annotator is not None
        capsys.readouterr()
        annotator.annotate_file(io_manager)

    captured = capsys.readouterr()

    print(captured.out)
    print(captured.err)
    assert captured.out == expected_cleanup_output
