from dae.pedigrees.layout import Layout


def assert_positions(expected, resulted):
    for expected_level, resulted_level in zip(expected, resulted):
        expected_level.sort(
            key=lambda layout: layout.individual.member.person_id
        )
        resulted_level.sort(
            key=lambda layout: layout.individual.member.person_id
        )

        for expected_layout, resulted_layout in zip(
            expected_level, resulted_level
        ):
            assert str(expected_layout) == str(resulted_layout)


def test_generate_layout(family1, family2):
    layout1 = Layout.from_family(family1)
    layout2 = Layout.from_family(family2)
    assert len(layout1) == 1
    assert len(layout2) == 1

    assert layout1[0].positions is not None
    assert layout2[0].positions is not None
    assert_positions(layout1[0].positions, layout2[0].positions)


def test_load_from_family_layout(family1, family2, layout2):
    layout1 = Layout.from_family_layout(family1)
    assert layout1 is None
    # assert len(layout1.positions) == 1

    layout2_loaded = Layout.from_family_layout(family2)
    assert layout2_loaded is not None
    assert_positions(layout2_loaded.positions, layout2.positions)
