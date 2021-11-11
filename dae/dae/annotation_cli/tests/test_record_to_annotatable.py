import pytest

from dae.annotation_cli.annotate_columns import build_record_to_annotatable
from dae.annotation.annotatable import Position, VCFAllele, Region


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
    assert build_record_to_annotatable({}, {}) is None
    assert build_record_to_annotatable({}, {"gosho": "pesho"}) is None
