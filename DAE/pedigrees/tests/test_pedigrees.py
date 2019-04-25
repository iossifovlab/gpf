def test_reading_pedigree_file(pedigree_test):
    assert pedigree_test is not None


def test_family_connections_can_be_created(fam1_family_connections):
    assert fam1_family_connections is not None


def test_sandwich_instance_can_be_created_for_fam1(fam1_family_connections):
    sandwich = fam1_family_connections.create_sandwich_instance()

    assert sandwich is not None
