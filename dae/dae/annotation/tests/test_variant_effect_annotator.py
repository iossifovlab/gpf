import pytest

from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.effect_annotator import VariantEffectAnnotator


@pytest.fixture(scope="session")
def effect_annotator(genomes_db_2013):
    options = {
        "vcf": True,
        "direct": False,
        "r": "reference",
        "a": "alternative",
        "c": "chrom",
        "p": "position",
        "prom_len": 0,
    }

    columns = {
        "effect_type": "effect_type_1",
        "effect_genes": "effect_genes_1",
        "effect_gene_genes": "effect_gene_genes_1",
        "effect_gene_types": "effect_gene_types_1",
        "effect_details": "effect_details_1",
        "effect_details_transcript_ids": "effect_details_transcript_ids_1",
        "effect_details_details": "effect_details_details_1",
    }

    config = AnnotationConfigParser.parse_section({
            "options": options,
            "columns": columns,
            "annotator": "effect_annotator.VariantEffectAnnotator",
            "virtual_columns": [],
        }
    )

    annotator = VariantEffectAnnotator(config, genomes_db_2013)
    assert annotator is not None

    return annotator


def test_effect_annotator(effect_annotator, variants_io, capsys):
    with variants_io("fixtures/effects_trio_multi-effect.txt") as io_manager:

        captured = capsys.readouterr()

        effect_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)

    print(effect_annotator.schema)
