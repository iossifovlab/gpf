# pylint: disable=W0621,C0114,C0116,W0212,W0613

def test_denovo_extra_attributes(denovo_extra_attr_loader):

    loader = denovo_extra_attr_loader
    fvs = list(loader.family_variants_iterator())
    print(fvs)
    for fv in fvs:
        for fa in fv.alt_alleles:
            print(fa.attributes, fa.summary_attributes)
            assert "someAttr" in fa.attributes

    fv = fvs[0]
    for fa in fv.alt_alleles:
        print(fa, fa.attributes, fa.summary_attributes)
        assert "someAttr" in fa.attributes
        assert fa.get_attribute("someAttr") == "asdf"

    fv = fvs[-1]
    for fa in fv.alt_alleles:
        print(fa.attributes, fa.summary_attributes)
        assert "someAttr" in fa.attributes
        assert fa.get_attribute("someAttr") == "adhglsfh"
