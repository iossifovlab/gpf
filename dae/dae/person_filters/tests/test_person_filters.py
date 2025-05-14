# pylint: disable=W0621,C0114,C0116,W0212,W0613
import dae.person_filters as pf
from dae.gpf_instance import GPFInstance


def test_family_filter(
    t4c8_instance: GPFInstance,
) -> None:
    filter_conf = {
        "source": "phenotype",
        "selection": {"selection": ["unaffected"]},
        "role": "dad",
    }
    pedigree_filter = pf.make_pedigree_filter(filter_conf)
    genotype_data = t4c8_instance.get_genotype_data("t4c8_study_1")
    ids = pedigree_filter.apply(genotype_data.families, ["dad"])
    assert ids == {"f1.1", "f1.3"}


def test_make_pedigree_filter() -> None:
    filter_conf = {
        "source": "pedigree_column",
        "selection": {"selection": ["some_value"]},
        "role": "prb",
    }
    pedigree_filter = pf.make_pedigree_filter(filter_conf)
    assert isinstance(pedigree_filter, pf.FamilyFilter)
    assert isinstance(pedigree_filter.person_filter, pf.PersonFilterSet)
    assert pedigree_filter.person_filter.criteria == "pedigree_column"
    assert pedigree_filter.person_filter.values == {"some_value"}
