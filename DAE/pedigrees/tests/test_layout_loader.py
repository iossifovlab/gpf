def assert_positions(expected, resulted):
    for expected_level, resulted_level in zip(expected, resulted):
        expected_level.sort(key=lambda layout: layout.individual.member.id)
        resulted_level.sort(key=lambda layout: layout.individual.member.id)

        for expected_layout, resulted_layout in\
                zip(expected_level, resulted_level):
            assert str(expected_layout) == str(resulted_layout)


def test_get_positions_from_family(
        layout_loader1, layout_loader2, layout_positions2):
    positions1 = layout_loader1.get_positions_from_family()
    layout_loader1.family_connections = None
    positions1_none = layout_loader1.get_positions_from_family()
    positions2 = layout_loader2.get_positions_from_family()

    assert positions1 is None
    assert positions1_none is None
    assert_positions(layout_positions2, positions2)


def test_load(layout_loader1, layout_loader2, loaded_layout2):
    positions1 = layout_loader1.load()
    positions2 = layout_loader2.load()

    assert positions1 is None
    assert_positions(loaded_layout2.positions, positions2.positions)
