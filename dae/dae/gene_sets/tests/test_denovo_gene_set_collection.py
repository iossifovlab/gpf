# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.gene_sets.denovo_gene_sets_db import DenovoGeneSetCollection
from dae.studies.study import GenotypeData


@pytest.mark.parametrize("gene_effects,person_fpids,dgsc_spec,count,syms", [
    ([("t4", "missense")], [("f1.1", "p1")],
     "Missense phenotype:autism", 1, {"t4"}),
    ([("t4", "missense")], [("f1.1", "p1")],
     "Missense.Recurrent phenotype:autism", 0, set()),
    ([("t4", "missense")], [("f1.1", "p1"), ("f1.3", "p3")],
     "Missense.Recurrent phenotype:autism", 1, {"t4"}),
    ([("t4", "missense")], [("f1.1", "p1"), ("f1.3", "p3")],
     "Missense.Single phenotype:autism", 0, set()),
    ([("t4", "missense")], [("f1.1", "p1"), ("f1.3", "p3")],
     "Missense.Female phenotype:autism", 1, {"t4"}),
    ([("t4", "missense")], [("f1.1", "p1"), ("f1.3", "p3")],
     "Missense.Male phenotype:autism", 0, set()),
])
def test_denovo_gene_set_collection_add_gene(
    t4c8_study_1: GenotypeData,
    gene_effects: list[tuple[str, str]],
    person_fpids: list[tuple[str, str]],
    dgsc_spec: str,
    count: int,
    syms: set[str],
) -> None:
    dgsc = DenovoGeneSetCollection.create_empty_collection(t4c8_study_1)
    assert dgsc is not None

    persons = [
        t4c8_study_1.families.persons[fpid]
        for fpid in person_fpids
    ]

    dgsc.add_gene(
        gene_effects,
        persons,
    )

    gs = dgsc.get_gene_set(dgsc_spec)
    assert gs is not None
    assert gs.count == count
    assert set(gs.syms) == syms
