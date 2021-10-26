from dae.annotation.allele import Allele


def test_position_allele():
    a = Allele.build_position_allele("1", 3)
    assert a.allele_type == Allele.Type.position
    assert a.pos_end == 3
