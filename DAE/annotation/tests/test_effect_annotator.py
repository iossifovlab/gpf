from __future__ import print_function, absolute_import

from box import Box

from annotation.tools.annotator_config import VariantAnnotatorConfig
from annotation.tools.effect_annotator import EffectAnnotator


def test_effect_annotator(variants_io, capsys):

    options = Box({
        "vcf": True,
        "direct": False,
        'r': 'reference',
        'a': 'alternative',
        'c': 'chrom',
        'p': 'position',

        # "c": "CSHL:chr",
        # "p": "CSHL:position",
        # "v": "CSHL:variant",
    }, default_box=True, default_box_attr=None)

    columns_config = {
        'effect_type': 'effectType',
        'effect_gene': 'effectGene',
        'effect_details': 'effectDetails'
    }

    config = VariantAnnotatorConfig(
        name="test_annotator",
        annotator_name="effect_annotator.EffectAnnotator",
        options=options,
        columns_config=columns_config,
        virtuals=[]
    )

    with variants_io("fixtures/effects_trio_multi-eff.txt") as io_manager:
        annotator = EffectAnnotator(config)
        assert annotator is not None

        captured = capsys.readouterr()

        annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)
