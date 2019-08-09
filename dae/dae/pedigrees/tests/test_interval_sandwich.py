def test_family_connections(family_connections_from_family2):
    assert family_connections_from_family2 is not None


def test_sandwich_instance(sandwich_instance_from_family2):
    assert sandwich_instance_from_family2 is not None
    assert len(sandwich_instance_from_family2.vertices) == 5
    assert len(sandwich_instance_from_family2.required_graph) == 5
    assert len(sandwich_instance_from_family2.forbidden_graph) == 5


def test_intervals(intervals_from_family2):
    assert intervals_from_family2 is not None
    assert len(intervals_from_family2) == 5


def test_individual_intervals(individuals_intervals_from_family2):
    assert len(individuals_intervals_from_family2) == 3
