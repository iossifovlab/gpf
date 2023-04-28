# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.variant_utils import mat2str


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "inheritance,count",
    [
        ("mendelian", 3),
        (["mendelian"], 3),
        ("omission", 4),
        ("denovo", 2),
        ("unknown", 14),
    ],
)
def test_inheritance_trio_full(variants_impl, variants, inheritance, count):
    fvars = variants_impl(variants)("backends/inheritance_trio")
    actual_variants = list(
        fvars.query_variants(inheritance=inheritance, return_reference=False)
    )
    for v in actual_variants:
        assert len(mat2str(v.best_state)) == 7
    assert len(actual_variants) == count


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "count,inheritance", [
        (7, "mendelian"),
        (7, ["mendelian", "not possible_denovo"]),
        (1, "omission"),
        (1, "denovo"),
    ]
)
def test_inheritance_quad_full(variants_impl, variants, count, inheritance):
    fvars = variants_impl(variants)("backends/inheritance_quad")
    actual_variants = list(
        fvars.query_variants(inheritance=inheritance, return_reference=False)
    )
    assert len(actual_variants) == count
    for v in actual_variants:
        assert len(mat2str(v.best_state)) == 9


@pytest.mark.parametrize("variants", ["variants_impala", "variants_vcf"])
@pytest.mark.parametrize(
    "count,inheritance",
    [(5, None), (4, "mendelian"), (0, "omission"), (1, "denovo"), ],
)
def test_inheritance_multi_full(variants_impl, variants, count, inheritance):
    fvars = variants_impl(variants)("backends/inheritance_multi")
    actual_variants = list(
        fvars.query_variants(inheritance=inheritance, return_reference=False)
    )
    for v in actual_variants:
        for aa in v.alleles:
            print(">>", aa, aa.inheritance_in_members)
    assert len(actual_variants) == count
