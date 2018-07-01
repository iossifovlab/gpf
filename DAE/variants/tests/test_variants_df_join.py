'''
Created on Jul 1, 2018

@author: lubo
'''


def test_fix_broken_trios2_11602_variants(variants_df):

    dfvars = variants_df("fixtures/trios2_11602")
    assert dfvars is not None

    vs = dfvars.query_variants()
    vs = list(vs)
    for v in vs:
        print(v)
    assert len(vs) == 2
    v0 = vs[0]
    v1 = vs[1]

    assert v0.summary_variant == v1.summary_variant
    sv = v0.summary_variant
    assert ",".join(sv.alts) == "G,A"
    assert ",".join(v0.alts) == "A"
    assert ",".join(v1.alts) == ""


def test_fix_broken_trios2_11605_variants(variants_df):

    dfvars = variants_df("fixtures/trios2_11605")
    assert dfvars is not None

    vs = dfvars.query_variants()
    vs = list(vs)
    for v in vs:
        print(v)
    assert len(vs) == 2
    v0 = vs[0]
    v1 = vs[1]

    assert v0.summary_variant == v1.summary_variant
    sv = v0.summary_variant
    assert ",".join(sv.alts) == "G,A"
    assert ",".join(v0.alts) == "G,A"
    assert ",".join(v1.alts) == "G,A"
