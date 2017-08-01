from collections import defaultdict
from functools import reduce


class PedigreeMemberWithCoordinates:

    def __init__(self, member, x=0, y=0, size=21, scale=1.0):
        self.member = member
        self.x = x
        self.y = y
        self.size = size
        self.scale = scale

    @property
    def center(self):
        return self.x + self.size / 2

    def __repr__(self):
        return "({}, {})".format(self.x, self.y)


class Line:

    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2


class Layout:

    def __init__(self, intervals):
        self._intervals = intervals
        self.lines = []
        self._individuals_by_rank = self._intervals_by_ranks()
        self._id_to_position = self._generate_simple_layout(
            self._individuals_by_rank)
        self._generate_from_intervals()

    def _generate_from_intervals(self):

        self._optimize_drawing()

    def _optimize_drawing(self):
        moved_individuals = -1
        counter = 1

        while(moved_individuals and counter < 100):
            moved_individuals = 0
            if counter % 6 < 3:
                moved_individuals += self._align_parens_of_children()
                moved_individuals += self._align_children_of_parents()
            else:
                moved_individuals += self._align_children_of_parents()
                moved_individuals += self._align_parens_of_children()

            moved_individuals += self._set_mates_equally_apart()
            moved_individuals += self._move_overlaps()

            counter += 1
        print("done", counter)
        self._align_left()

    def _align_left(self, x_offset=10):
        min_x = min([i.x for i in self._id_to_position.values()])

        for individual in self._id_to_position.values():
            individual.x = individual.x - min_x + x_offset

    def _set_mates_equally_apart(self):
        moved = 0

        for level in self._individuals_by_rank:
            mating_units = self._get_mates_on_level(level)

            dual_mating_units = {(mu1, mu2) for mu1 in mating_units
                                 for mu2 in mating_units
                                 if (mu1.father is mu2.father) ^
                                    (mu1.mother is mu2.mother)}

            for mu1, mu2 in dual_mating_units:
                ordered_parents = []

                if mu1.father is mu2.father:
                    ordered_parents = [mu1.mother, mu1.father, mu2.mother]
                else:
                    ordered_parents = [mu1.father, mu1.mother, mu2.father]

                ordered_parents = map(lambda i: self._id_to_position[i],
                                      ordered_parents)
                if ordered_parents[0].x > ordered_parents[2].x:
                    ordered_parents[0], ordered_parents[2] = \
                        ordered_parents[2], ordered_parents[0]

                dist1 = ordered_parents[1].x - ordered_parents[0].x
                dist2 = ordered_parents[1].x - ordered_parents[0].x

                if dist1 < 0 or dist2 < 0 or abs(dist1 - dist2) < 1e-7:
                    return 0

                if dist1 > dist2:
                    moved += self._move(ordered_parents[2:], dist1 - dist2)
                else:
                    moved += self._move(ordered_parents[1:], dist2 - dist1)

        return moved

    def _move_overlaps(self, gap_size=8):
        moved = 0
        first_individual_position = self._id_to_position[
            self._individuals_by_rank[0][0]]
        min_gap = first_individual_position.size + gap_size

        for level in self._individuals_by_rank:
            level_with_positions = map(lambda i: self._id_to_position[i],
                                       level)
            for index, individual1 in enumerate(level_with_positions):
                for individual2 in level_with_positions[index+1:index+2]:
                    diff = abs(individual1.x - individual2.x)
                    assert diff >= 0
                    if diff < min_gap:
                        moved += self._move([individual1, individual2],
                                            min_gap - diff)

        return moved

    def _align_children_of_parents(self):
        moved = 0

        for level in self._individuals_by_rank:
            mating_units = self._get_mates_on_level(level)

            for mates in mating_units:
                moved += self._center_children_of_parents(mates)

        return moved

    def _center_children_of_parents(self, mating_unit):
        children = self._get_first_and_last_children_positions(mating_unit)

        children_center = (children[0].x + children[1].x) / 2

        mother = self._id_to_position[mating_unit.mother]
        father = self._id_to_position[mating_unit.father]

        parents_center = (father.x + mother.x) / 2

        offset = parents_center - children_center

        if abs(offset) > 0.0001:
            return self._move(children, offset)

        return 0

    def _align_parens_of_children(self):
        moved = 0

        for level in self._individuals_by_rank:
            sibship_groups = self._get_sibships_on_level(level)
            for sibship in sibship_groups:
                moved += self._center_parents_of_children(sibship)

        return moved

    def _center_parents_of_children(self, sibship):
        assert len(sibship) > 0

        some_child = sibship[0]

        start_x = self._id_to_position[some_child].x
        end_x = self._id_to_position[sibship[len(sibship) - 1]].x

        children_center = (start_x + end_x) / 2

        mother = some_child.parents.mother
        father = some_child.parents.father

        mother_position = self._id_to_position[mother]
        father_position = self._id_to_position[father]

        parents_center = (mother_position.x + father_position.x) / 2

        offset = children_center - parents_center

        if offset != 0:
            return self._move([mother_position, father_position], offset)
        return 0

    def _move(self, individuals, offset, already_moved=set()):
        assert len(individuals) > 0
        min_individual = reduce(lambda a, b: a if a.x < b.x else b,
                                individuals)
        max_individual = reduce(lambda a, b: a if a.x > b.x else b,
                                individuals)

        level = self._get_level_of_individual(min_individual.member)

        individuals = level[level.index(min_individual.member):
                            level.index(max_individual.member) + 1]

        individuals = list(set(individuals) - already_moved)

        if len(individuals) == 0:
            return 0

        to_move = set()
        to_move_offset = 0

        if offset > 0:
            start = min_individual.x
            end = max_individual.x
            new_end = end + offset
            to_move = {i for x in level for i in [self._id_to_position[x]]
                       if i.x >= start and i.x <= new_end}
            to_move -= already_moved

            if len(to_move) != 0:
                to_move_offset = max(map(
                    lambda x: new_end - x.center + 8*2 + x.size,
                    to_move))
        else:
            start = min_individual.x
            end = max_individual.x
            new_start = start + offset
            to_move = {i for x in level for i in [self._id_to_position[x]]
                       if i.x >= new_start and i.x <= end}
            to_move -= already_moved

            if len(to_move) != 0:
                to_move_offset = min(map(
                    lambda x: new_start - x.center + 8*2 + x.size,
                    to_move))

        for individual in individuals:
            position = self._id_to_position[individual]
            position.x += offset

        other_moved = 0
        if to_move != set():
            other_moved = self._move(
                to_move, to_move_offset, already_moved | set(individuals))

        return len(individuals) + other_moved

    def _get_mates_on_level(self, level):
        return {mu for i in level for mu in i.mating_units}

    def _get_first_and_last_children_positions(self, mating_unit):
        children = mating_unit.children.individuals
        children_positions = map(lambda x: self._id_to_position[x],
                                 children)
        children_positions = sorted(children_positions, key=lambda x: x.x)

        return [children_positions[0],
                children_positions[len(children_positions) - 1]]

    def _get_sibships_on_level(self, level):
        individuals_with_parents = filter(lambda i: bool(i.parents),
                                          level)

        def reducer(acc, x):
            if len(acc) == 0:
                return [[x]]
            last_array = acc[len(acc) - 1]
            if x.are_siblings(last_array[0]):
                last_array.append(x)
            else:
                acc.append([x])

            return acc

        return reduce(reducer, individuals_with_parents, [])

    def _get_level_of_individual(self, individual):
        for individuals_on_level in self._individuals_by_rank:
            if individual in individuals_on_level:
                return individuals_on_level

        return None

    def _generate_simple_layout(self, levels, level_heigh=30,
                                x_offset=20, y_offset=20, gap=8):
        result = {}
        original_x_offset = x_offset

        for rank, individuals in enumerate(levels):
            x_offset = original_x_offset
            for individual in individuals:
                position = PedigreeMemberWithCoordinates(
                    individual, x_offset, (rank + 1) * level_heigh + y_offset)
                result[individual] = position

                x_offset += position.size + gap

        return result

    def _intervals_by_ranks(self):
        result = []

        rank_to_individuals = defaultdict(list)
        for interval in self._intervals:
            rank_to_individuals[interval.vertex.rank].append(interval)

        for key in sorted(rank_to_individuals.keys()):
            sorted_intervals = sorted(rank_to_individuals[key],
                                      key=lambda x: (x.left, x.right))
            result.append(map(lambda x: x.vertex, sorted_intervals))

        return result
