# pylint: disable=W0621,C0114,C0116,W0212,W0613
import dae.person_filters as pf
from dae.gpf_instance import GPFInstance


def test_family_filter(
    fixtures_gpf_instance: GPFInstance,
) -> None:
    filter_conf = {
        "source": "phenotype",
        "selection": {"selection": ["unaffected"]},
        "role": "dad",
    }
    pedigree_filter = pf.make_pedigree_filter(filter_conf)
    genotype_data = fixtures_gpf_instance.get_genotype_data("Study1")
    ids = pedigree_filter.apply(genotype_data.families, ["dad"])
    assert ids == {"f1", "f3", "f6", "f11"}


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
    assert pedigree_filter.person_filter.values == {"some_value"}  # noqa: PD011
