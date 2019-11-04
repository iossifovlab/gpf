def test_layout(layout_from_family2):
    assert layout_from_family2 is not None


def test_layout__intervals(
        layout_from_family2, individuals_intervals_from_family2):
    assert layout_from_family2._intervals == individuals_intervals_from_family2


def test_layout_lines(layout_from_family2):
    assert len(layout_from_family2.lines) == 3

    assert layout_from_family2.lines[0].x1 == 31.0
    assert layout_from_family2.lines[0].y1 == 60.5
    assert layout_from_family2.lines[0].x2 == 53.5
    assert layout_from_family2.lines[0].y2 == 60.5
    assert layout_from_family2.lines[0].curved is False
    assert layout_from_family2.lines[0].curve_base_height is None

    assert layout_from_family2.lines[1].x1 == 42.25
    assert layout_from_family2.lines[1].y1 == 60.5
    assert layout_from_family2.lines[1].x2 == 42.25
    assert layout_from_family2.lines[1].y2 == 75.5
    assert layout_from_family2.lines[1].curved is False
    assert layout_from_family2.lines[1].curve_base_height is None

    assert layout_from_family2.lines[2].x1 == 42.25
    assert layout_from_family2.lines[2].y1 == 80.0
    assert layout_from_family2.lines[2].x2 == 42.25
    assert layout_from_family2.lines[2].y2 == 75.5
    assert layout_from_family2.lines[2].curved is False
    assert layout_from_family2.lines[2].curve_base_height is None


def test_layout_positions(layout_from_family2):
    assert len(layout_from_family2.positions) == 2
    assert len(layout_from_family2.positions[0]) == 2

    assert layout_from_family2.positions[0][0].individual.member.person_id == 'mom2'
    assert layout_from_family2.positions[0][0].x == 10.0
    assert layout_from_family2.positions[0][0].y == 50.0
    assert layout_from_family2.positions[0][0].size == 21.0
    assert layout_from_family2.positions[0][0].scale == 1.0

    assert layout_from_family2.positions[0][1].individual.member.person_id == 'dad2'
    assert layout_from_family2.positions[0][1].x == 53.5
    assert layout_from_family2.positions[0][1].y == 50.0
    assert layout_from_family2.positions[0][1].size == 21.0
    assert layout_from_family2.positions[0][1].scale == 1.0

    assert len(layout_from_family2.positions[1]) == 1
    assert layout_from_family2.positions[1][0].individual.member.person_id == 'id2'
    assert layout_from_family2.positions[1][0].x == 31.75
    assert layout_from_family2.positions[1][0].y == 80.0
    assert layout_from_family2.positions[1][0].size == 21.0
    assert layout_from_family2.positions[1][0].scale == 1.0


def test_layout__individuals_by_rank(layout_from_family2):
    assert len(layout_from_family2._individuals_by_rank) == 2

    assert len(layout_from_family2._individuals_by_rank[0]) == 2
    assert layout_from_family2._individuals_by_rank[0][0].member.person_id == 'mom2'
    assert layout_from_family2._individuals_by_rank[0][1].member.person_id == 'dad2'

    assert len(layout_from_family2._individuals_by_rank[1]) == 1
    assert layout_from_family2._individuals_by_rank[1][0].member.person_id == 'id2'


def test_layout__id_to_position(layout_from_family2):
    assert len(layout_from_family2._id_to_position) == 3
    assert layout_from_family2._id_to_position[
        layout_from_family2._individuals_by_rank[0][0]]\
        .individual.member.person_id == 'mom2'
    assert layout_from_family2._id_to_position[
        layout_from_family2._individuals_by_rank[0][1]]\
        .individual.member.person_id == 'dad2'
    assert layout_from_family2._id_to_position[
        layout_from_family2._individuals_by_rank[1][0]]\
        .individual.member.person_id == 'id2'


def test_layout_id_to_position(layout_from_family2):
    assert len(layout_from_family2.id_to_position) == 3
    assert layout_from_family2.id_to_position['mom2']\
                              .individual.member.person_id == 'mom2'
    assert layout_from_family2.id_to_position['dad2']\
                              .individual.member.person_id == 'dad2'
    assert layout_from_family2.id_to_position['id2']\
                              .individual.member.person_id == 'id2'


def test_layout_individuals_by_rank(layout_from_family2):
    assert len(layout_from_family2.individuals_by_rank) == 3
    assert layout_from_family2.individuals_by_rank['mom2'] == 1
    assert layout_from_family2.individuals_by_rank['dad2'] == 1
    assert layout_from_family2.individuals_by_rank['id2'] == 2
