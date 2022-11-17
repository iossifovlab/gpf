from studies.remote_study import RemoteGenotypeData

def test_remote_genotype_study(rest_client):
    study = RemoteGenotypeData("iossifov_2014", rest_client)

    assert study.is_group is False


def test_remote_genotype_dataset(rest_client):
    study = RemoteGenotypeData("test_dataset", rest_client)

    assert study.is_group is True
