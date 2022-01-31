import pytest

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance_agp",
    "dae_calc_gene_sets",
)

route_prefix = "/api/v3/autism_gene_tool"


def test_configuration(admin_client):
    response = admin_client.get(f"{route_prefix}/single-view/configuration")

    assert response.status_code == 200
    print(response.data)

    assert len(response.data["genomicScores"]) == 2

    assert len(response.data["genomicScores"][0]["scores"]) == 3
    assert response.data["genomicScores"][0]["category"] == \
        "protection_scores"

    assert len(response.data["genomicScores"][1]["scores"]) == 3
    assert response.data["genomicScores"][1]["category"] == "autism_scores"

    datasets = response.data["datasets"]
    assert len(datasets) == 1
    assert datasets[0]["id"] == "iossifov_we2014_test"
    assert len(datasets[0]["statistics"]) == 2
    assert len(datasets[0]["personSets"]) == 2
    assert datasets[0]["personSets"] == [
        {
            "id": "unknown",
            "displayName": "unknown",
            "collectionId": "phenotype",
            "description": "",
            "parentsCount": 0,
            "childrenCount": 11,
            "statistics": [
                {
                    'id': 'denovo_noncoding',
                    'displayName': 'Noncoding',
                    'effects': ['noncoding'],
                    'category': 'denovo'
                },
                {
                    'id': 'denovo_missense',
                    'displayName': 'Missense',
                    'effects': ['missense'],
                    'category': 'denovo'
                }
            ]
        },
        {
            "id": "unaffected",
            "displayName": "unaffected",
            "collectionId": "phenotype",
            "description": "",
            "parentsCount": 22,
            "childrenCount": 10,
            "statistics": [
                {
                    'id': 'denovo_noncoding',
                    'displayName': 'Noncoding',
                    'effects': ['noncoding'],
                    'category': 'denovo'
                },
                {
                    'id': 'denovo_missense',
                    'displayName': 'Missense',
                    'effects': ['missense'],
                    'category': 'denovo'
                }
            ]
        }
    ]


def test_get_statistic(admin_client):
    response = admin_client.get(f"{route_prefix}/single-view/gene/CHD8")
    assert response.status_code == 200
    print(response.data)


def test_get_table_config(admin_client):
    response = admin_client.get(f"{route_prefix}/table/configuration")
    assert response.status_code == 200
    print(response.data)


def test_get_statistics(admin_client):
    response = admin_client.get(f"{route_prefix}/table/rows")
    assert response.status_code == 200
    print(response.data)