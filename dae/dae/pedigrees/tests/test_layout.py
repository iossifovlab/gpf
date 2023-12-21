# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.pedigrees.pedigrees import IntervalForVertex
from dae.pedigrees.layout import Layout


def test_layout(layout_from_family2: list[Layout]) -> None:
    assert layout_from_family2 is not None


def test_layout__intervals(
    layout_from_family2: list[Layout],
    individuals_intervals_from_family2: list[IntervalForVertex]
) -> None:
    assert layout_from_family2[0]._intervals == \
        individuals_intervals_from_family2


def test_layout_lines(layout_from_family2: list[Layout]) -> None:
    layout = layout_from_family2[0]

    assert len(layout.lines) == 3

    assert layout.lines[0].x1 == 31.0
    assert layout.lines[0].y1 == 60.5
    assert layout.lines[0].x2 == 53.5
    assert layout.lines[0].y2 == 60.5
    assert layout.lines[0].curved is False
    assert layout.lines[0].curve_base_height is None
    assert layout.lines[1].x1 == 42.25
    assert layout.lines[1].y1 == 60.5
    assert layout.lines[1].x2 == 42.25
    assert layout.lines[1].y2 == 75.5
    assert layout.lines[1].curved is False
    assert layout.lines[1].curve_base_height is None
    assert layout.lines[2].x1 == 42.25
    assert layout.lines[2].y1 == 80.0
    assert layout.lines[2].x2 == 42.25
    assert layout.lines[2].y2 == 75.5
    assert layout.lines[2].curved is False
    assert layout.lines[2].curve_base_height is None


def test_layout_positions(layout_from_family2: list[Layout]) -> None:
    layout = layout_from_family2[0]

    assert len(layout.positions) == 2
    assert len(layout.positions[0]) == 2

    assert layout.positions[0][0].individual.member is not None
    assert (
        layout.positions[0][0].individual.member.person_id
        == "mom2"
    )
    assert layout.positions[0][0].x == 10.0
    assert layout.positions[0][0].y == 50.0
    assert layout.positions[0][0].size == 21.0

    assert layout.positions[0][1].individual.member is not None
    assert (
        layout.positions[0][1].individual.member.person_id
        == "dad2"
    )
    assert layout.positions[0][1].x == 53.5
    assert layout.positions[0][1].y == 50.0
    assert layout.positions[0][1].size == 21.0

    assert len(layout.positions[1]) == 1
    assert layout.positions[1][0].individual.member is not None
    assert (
        layout.positions[1][0].individual.member.person_id
        == "id2"
    )
    assert layout.positions[1][0].x == 31.75
    assert layout.positions[1][0].y == 80.0
    assert layout.positions[1][0].size == 21.0


def test_layout__individuals_by_rank(
    layout_from_family2: list[Layout]
) -> None:
    layout = layout_from_family2[0]

    assert len(layout._individuals_by_rank) == 2

    assert len(layout._individuals_by_rank[0]) == 2
    assert layout._individuals_by_rank[0][0].member is not None
    assert (
        layout._individuals_by_rank[0][0].member.person_id
        == "mom2"
    )
    assert layout._individuals_by_rank[0][1].member is not None
    assert (
        layout._individuals_by_rank[0][1].member.person_id
        == "dad2"
    )

    assert len(layout._individuals_by_rank[1]) == 1
    assert layout._individuals_by_rank[1][0].member is not None
    assert (
        layout._individuals_by_rank[1][0].member.person_id
        == "id2"
    )


def test_layout__id_to_position(layout_from_family2: list[Layout]) -> None:
    layout = layout_from_family2[0]

    assert len(layout._id_to_position) == 3

    individual_member = layout._id_to_position[
        layout._individuals_by_rank[0][0]].individual.member
    assert individual_member is not None
    assert individual_member.person_id == "mom2"

    individual_member = layout._id_to_position[
        layout._individuals_by_rank[0][1]].individual.member
    assert individual_member is not None
    assert individual_member.person_id == "dad2"

    individual_member = layout._id_to_position[
        layout._individuals_by_rank[1][0]
    ].individual.member
    assert individual_member is not None
    assert individual_member.person_id == "id2"


def test_layout_id_to_position(layout_from_family2: list[Layout]) -> None:
    layout = layout_from_family2[0]

    assert len(layout.id_to_position) == 3
    individual_member = layout.id_to_position["mom2"].individual.member
    assert individual_member is not None
    assert individual_member.person_id == "mom2"

    individual_member = layout.id_to_position["dad2"].individual.member
    assert individual_member is not None
    assert individual_member.person_id == "dad2"

    individual_member = layout.id_to_position["id2"].individual.member
    assert individual_member is not None
    assert individual_member.person_id == "id2"


def test_layout_individuals_by_rank(layout_from_family2: list[Layout]) -> None:
    layout = layout_from_family2[0]

    assert len(layout.individuals_by_rank) == 3
    assert layout.individuals_by_rank["mom2"] == 1
    assert layout.individuals_by_rank["dad2"] == 1
    assert layout.individuals_by_rank["id2"] == 2
