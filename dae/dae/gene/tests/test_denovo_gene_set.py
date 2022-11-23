# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory
from dae.gene.denovo_gene_set_collection import \
    DenovoGeneSetCollection

pytestmark = pytest.mark.usefixtures("gene_info_cache_dir", "calc_gene_sets")


def test_get_person_set_collection_legend(denovo_gene_set_f4):
    dgsl = denovo_gene_set_f4.get_person_set_collection_legend("phenotype")
    print(dgsl)
    assert len(dgsl) == 2


def test_get_person_set_collection_legend_missing(denovo_gene_set_f4):
    dgsl = denovo_gene_set_f4.get_person_set_collection_legend("missing")

    assert len(dgsl) == 0


def test_get_gene_sets_types_legend(denovo_gene_set_f4):
    dgstl = denovo_gene_set_f4.get_gene_sets_types_legend()

    assert len(dgstl) == 1
    assert dgstl[0]["datasetId"] == "f4_trio"
    assert dgstl[0]["datasetName"] == "f4_trio"
    assert dgstl[0]["personSetCollectionId"] == "phenotype"
    assert dgstl[0]["personSetCollectionName"] == "Phenotype"
    assert len(dgstl[0]["personSetCollectionLegend"]) == 2


@pytest.fixture
def trios2_dgsc(trios2_study):
    DenovoGeneSetCollectionFactory.build_collection(trios2_study)
    dgsc = DenovoGeneSetCollectionFactory.load_collection(trios2_study)
    return dgsc


def test_denovo_gene_sets_legend(trios2_dgsc):
    assert trios2_dgsc is not None
    legend = trios2_dgsc.get_gene_sets_types_legend()
    assert len(legend) == 1
    assert legend[0]["datasetId"] == "trios2"
    assert legend[0]["datasetName"] == "trios2"
    assert legend[0]["personSetCollectionId"] == "status"
    assert legend[0]["personSetCollectionName"] == "Affected Status"
    assert legend[0]["personSetCollectionLegend"] == [
        {"id": "affected", "name": "affected",
         "values": ["affected"], "color": "#e35252"},
        {"id": "unaffected", "name": "unaffected",
         "values": ["unaffected"], "color": "#ffffff"}
    ]


# 'affected': {
# 'LGDs':{'F': {}, 'M': {'g1': {'f1'}, 'g2': {'f2'}}, 'U': {}},
# 'Missense':{'F': {'g1': {'f1'}}, 'M': {'g1': {'f1', 'f2'}}, 'U': {}},
# 'Synonymous':{'F': {}, 'M': {'g2': {'f2'}}, 'U': {}}},
# 'unaffected': {
# 'LGDs':{'F': {}, 'M': {}, 'U': {}},
# 'Missense':{'F': {'g1': {'f1'}, 'g2': {'f1'}}, 'M': {'g1': {'f1'}}, 'U': {}},
# 'Synonymous':{'F': {}, 'M': {}, 'U': {}}

@pytest.mark.parametrize(
    "denovo_gene_set,people_groups,count",
    [
        ("LGDs", ["affected"], 2),
        ("LGDs.Male", ["affected"], 2),
        ("Missense", ["affected"], 1),
        ("Missense.Female", ["affected"], 1),
        ("Missense.Male", ["affected"], 1),
        ("Missense", ["affected", "unaffected"], 2),
        ("Missense", ["unaffected"], 2),
        ("Missense.Female", ["unaffected"], 2),
        ("Synonymous", ["affected"], 1),

    ],
)
def test_get_denovo_gene_set(
        trios2_dgsc, denovo_gene_set, people_groups, count):
    dgs = DenovoGeneSetCollection.get_gene_set(
        denovo_gene_set, [trios2_dgsc], {"trios2": {"status": people_groups}}
    )
    assert dgs is not None
    assert dgs["count"] == count
    assert dgs["name"] == denovo_gene_set
    assert dgs["desc"] == \
        f"{denovo_gene_set} (trios2:status:{','.join(people_groups)})"
