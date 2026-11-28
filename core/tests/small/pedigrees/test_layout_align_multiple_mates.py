# pylint: disable=C0114,C0116,W0212
import pytest

from gpf.pedigrees.family import Person
from gpf.pedigrees.layout import IndividualWithCoordinates, Layout
from gpf.pedigrees.pedigrees import Individual, MatingUnit


def _individual(person_id: str, sex: str) -> Individual:
    return Individual(member=Person(
        person_id=person_id,
        family_id="fam",
        mom_id="0",
        dad_id="0",
        sex=sex,
        status="1",
        role="unknown",
        generated=False,
    ))


class _Level:
    """One level of a layout with a husband and the wives of the husband."""

    def __init__(
        self,
        positions: list[tuple[str, float]],
        wives: list[str],
        husband: str = "h",
    ) -> None:
        self.by_id = {
            person_id: _individual(
                person_id, "1" if person_id == husband else "2")
            for person_id, _ in positions
        }
        self.husband = self.by_id[husband]
        for wife in wives:
            MatingUnit(self.by_id[wife], self.husband)
        self.level = [self.by_id[person_id] for person_id, _ in positions]
        self.layout = Layout()
        self.layout._id_to_position = {
            individual: IndividualWithCoordinates(individual, x, 0.0)
            for individual, (_, x) in zip(self.level, positions, strict=True)
        }
        self.layout._individuals_by_rank = [self.level]

    def align(self) -> int:
        return self.layout._align_multiple_mates_of_individual(
            self.husband, self.level)

    def x(self, person_id: str) -> float:
        return self.layout._id_to_position[self.by_id[person_id]].x


def test_left_far_mate_with_narrow_arch_moves_left() -> None:
    level = _Level(
        [("w1", 0.0), ("w2", 30.0), ("h", 60.0), ("w3", 90.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 1
    assert level.x("w1") == -42.0


def test_nearest_mates_never_move() -> None:
    level = _Level(
        [("w1", 0.0), ("w2", 30.0), ("h", 60.0), ("w3", 90.0)],
        wives=["w1", "w2", "w3"])

    level.align()

    assert (level.x("w2"), level.x("h"), level.x("w3")) == (30.0, 60.0, 90.0)


def test_left_far_mates_compare_with_the_next_mate_farthest_first() -> None:
    # w1 compares with w2 and moves first, then w2 compares with w3.
    level = _Level(
        [("w1", 0.0), ("w2", 30.0), ("w3", 60.0), ("h", 90.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 2
    assert (level.x("w1"), level.x("w2"), level.x("w3")) == (
        -72.0, -12.0, 60.0)


def test_left_far_mate_at_twice_compare_width_moves_nothing() -> None:
    # At equality the offset is 0, so `<` and `<=` give the same result.
    level = _Level(
        [("w1", -42.0), ("w2", 30.0), ("h", 60.0), ("w3", 90.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 0
    assert level.x("w1") == -42.0


def test_left_far_mate_with_wide_arch_stays() -> None:
    level = _Level(
        [("w1", -100.0), ("w2", 30.0), ("h", 60.0), ("w3", 90.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 0
    assert level.x("w1") == -100.0


def test_right_far_mate_with_narrow_arch_moves_right() -> None:
    level = _Level(
        [("w3", -30.0), ("h", 0.0), ("w1", 30.0), ("w2", 60.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 1
    assert level.x("w2") == 102.0
    assert level.x("w1") == 30.0


def test_right_far_mates_compare_with_the_next_mate_farthest_first() -> None:
    # w1 compares with w2 and moves first, then w2 compares with w3.
    level = _Level(
        [("h", 0.0), ("w3", 30.0), ("w2", 60.0), ("w1", 90.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 2
    assert (level.x("w1"), level.x("w2"), level.x("w3")) == (
        162.0, 102.0, 30.0)


def test_right_far_mate_at_twice_compare_width_moves_nothing() -> None:
    # At equality the offset is 0, so `<` and `<=` give the same result.
    level = _Level(
        [("w3", -30.0), ("h", 0.0), ("w1", 30.0), ("w2", 102.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 0
    assert level.x("w2") == 102.0


def test_right_far_mate_with_wide_arch_stays() -> None:
    level = _Level(
        [("w3", -30.0), ("h", 0.0), ("w1", 30.0), ("w2", 200.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 0
    assert level.x("w2") == 200.0


def test_one_mate_on_each_side_moves_nothing() -> None:
    level = _Level(
        [("w1", 0.0), ("h", 30.0), ("w2", 60.0)],
        wives=["w1", "w2"])

    moved = level.align()

    assert moved == 0
    assert (level.x("w1"), level.x("w2")) == (0.0, 60.0)


def test_mate_of_two_mating_units_counts_once() -> None:
    level = _Level(
        [("w1", 0.0), ("w2", 30.0), ("h", 60.0)],
        wives=["w1", "w1", "w2"])

    moved = level.align()

    assert moved == 1
    assert level.x("w1") == -42.0


def test_move_counts_and_shifts_an_individual_in_the_way() -> None:
    level = _Level(
        [("x0", -20.0), ("w1", 0.0), ("w2", 30.0), ("h", 60.0),
         ("w3", 90.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 2
    assert (level.x("x0"), level.x("w1")) == (-79.0, -42.0)


def test_offset_below_move_tolerance_moves_nothing() -> None:
    level = _Level(
        [("w1", -42.0 + 1e-6), ("w2", 30.0), ("h", 60.0), ("w3", 90.0)],
        wives=["w1", "w2", "w3"])

    moved = level.align()

    assert moved == 0
    assert level.x("w1") == -42.0 + 1e-6


def test_sides_come_from_the_order_of_the_level_not_from_x() -> None:
    # w1 and w2 lie left of h by x, but right of h in the level order.
    level = _Level(
        [("h", 60.0), ("w2", 30.0), ("w1", 0.0)],
        wives=["w1", "w2"])

    moved = level.align()

    assert moved == 3
    assert (level.x("w1"), level.x("w2"), level.x("h")) == (
        42.0, 79.0, 116.0)


def test_mate_missing_from_level_raises_value_error() -> None:
    level = _Level(
        [("w1", 0.0), ("w2", 30.0), ("h", 60.0)],
        wives=["w1", "w2"])
    stranger = _individual("s", "2")
    MatingUnit(stranger, level.husband)

    with pytest.raises(ValueError, match="not in list"):
        level.align()
