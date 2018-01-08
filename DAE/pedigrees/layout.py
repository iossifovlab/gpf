from collections import defaultdict
from functools import reduce


class IndividualWithCoordinates:

    def __init__(self, individual, x=0.0, y=0.0, size=21.0, scale=1.0):
        self.individual = individual
        self.x = x
        self.y = y
        self.size = size
        self.scale = scale

    @property
    def x_center(self):
        return self.x + self.size / 2.0

    @property
    def y_center(self):
        return self.y + self.size / 2.0

    def __repr__(self):
        return "({}, {})".format(self.x, self.y)


class Line:

    def __init__(self, x1, y1, x2, y2, curved=False, curve_base_height=None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.curved = curved
        self.curve_base_height = curve_base_height

        assert self.curved == (self.curve_base_height is not None)

    def curve_p0(self):
        return (self.x1, self.y1)

    def curve_p1(self):
        return (self.x1 + 10, self.y1 + self.curve_base_height*3.0)

    def curve_p2(self):
        return (self.x2, self.y2)

    def curve_p3(self):
        return (self.x2, self.y2)

    def inverse_curve_p1(self):
        return (self.x1 - 10, self.y1 - self.curve_base_height*3.0)

    def inverse_curve_p2(self):
        return (self.x2, self.y2)

    def curve_y_at(self, t):
        assert 0 <= t <= 1

        one_minus_t = 1.0 - t

        return (one_minus_t**3) * self.curve_p0()[1] + \
            3 * (one_minus_t**2) * t * self.curve_p1()[1] + \
            3 * one_minus_t * (t**2) * self.curve_p2()[1] + \
            (t**3) * self.curve_p3()[1]

    def inverse_curve_y_at(self, t):
        assert 0 <= t <= 1

        one_minus_t = 1.0 - t

        return (one_minus_t**3) * self.curve_p0()[1] + \
            3 * (one_minus_t**2) * t * self.inverse_curve_p1()[1] + \
            3 * one_minus_t * (t**2) * self.inverse_curve_p2()[1] + \
            (t**3) * self.curve_p3()[1]

    def __repr__(self):
        return "[({},{}) - ({},{})]".format(self.x1, self.y1, self.x2, self.y2)


class Layout:

    def __init__(self, intervals):
        self._intervals = intervals
        self.lines = []
        self.positions = []
        self._individuals_by_rank = self._intervals_by_ranks()
        self._id_to_position = self._generate_simple_layout(
            self._individuals_by_rank)
        self._generate_from_intervals()

    def _generate_from_intervals(self):

        self._optimize_drawing()
        self._create_positioned_individuals()
        self._create_lines()

    def _optimize_drawing(self, max_iter=50):
        # for level in self._individuals_by_rank:
        #     print(level)
        moved_individuals = -1
        counter = 1

        while moved_individuals and counter < max_iter:
            # print
            # print("new iter")
            moved_individuals = 0
            if counter % 6 < 3:
                moved_individuals += self._align_parents_of_children()
                # print(moved_individuals, "aligned parents of children")
                moved_individuals += self._align_children_of_parents()
                # print(moved_individuals, "aligned children of parents")
                moved_individuals += self._align_multiple_mates()
            else:
                moved_individuals += self._align_children_of_parents()
                # print(moved_individuals, "aligned children of parents")
                moved_individuals += self._align_parents_of_children()
                # print(moved_individuals, "aligned parents of children")
                moved_individuals += self._align_multiple_mates()

            # moved_individuals += self._set_mates_equally_apart()
            # print(moved_individuals, "set mates equally apart")
            moved_individuals += self._move_overlaps()
            # print(moved_individuals, "moved overlapping individuals")

            counter += 1
        print("done", counter)
        self._align_left()

    def _create_positioned_individuals(self):
        for level in self._individuals_by_rank:
            self.positions.append(
                map(lambda x: self._id_to_position[x], level))

    def _create_lines(self, y_offset=15):
        for level in self.positions:
            for start, individual in enumerate(level):
                if individual.individual.parents:
                    self.lines.append(Line(
                        individual.x_center, individual.y,
                        individual.x_center, individual.y_center - y_offset
                    ))

                for i, other_individual in enumerate(level[start+1:]):
                    are_next_to_eachother = (i == 0)
                    if (individual.individual.are_mates(
                            other_individual.individual)):
                        middle_x = (individual.x_center +
                                    other_individual.x_center) / 2.0
                        if are_next_to_eachother:
                            self.lines.append(Line(
                                individual.x + individual.size,
                                individual.y_center,
                                other_individual.x, other_individual.y_center
                            ))
                            self.lines.append(Line(
                                middle_x, individual.y_center,
                                middle_x, individual.y_center + y_offset
                            ))
                            continue

                        line = Line(
                            individual.x + individual.size,
                            individual.y_center,
                            other_individual.x, other_individual.y_center,
                            True, y_offset
                        )
                        self.lines.append(line)

                        percent_x = \
                            (middle_x - individual.x_center) / \
                            (other_individual.x_center - individual.x_center)
                        center_y = line.inverse_curve_y_at(percent_x)

                        self.lines.append(Line(
                            middle_x, center_y,
                            middle_x, individual.y_center + y_offset
                        ))

            i = 0
            while i < len(level) - 1:
                j = len(level) - 1
                while i < j:
                    individual = level[i]
                    other_individual = level[j]
                    if (individual.individual.are_siblings(
                            other_individual.individual)):
                        self.lines.append(Line(
                            individual.x_center, individual.y_center - y_offset,
                            other_individual.x_center,
                            other_individual.y_center - y_offset
                        ))
                        i = j
                        break
                    j -= 1
                i += 1

    def _align_left(self, x_offset=10):
        min_x = min([i.x for i in self._id_to_position.values()])

        for individual in self._id_to_position.values():
            individual.x = individual.x - min_x + x_offset

    def _align_multiple_mates(self):
        moved = 0
        for level in self._individuals_by_rank:
            for individual in level:
                if len(individual.mating_units) > 2:
                    moved += self._align_multiple_mates_of_individual(
                        individual, level)

        return moved

    def _align_multiple_mates_of_individual(self, individual, level):
        moved = 0

        others = {mu.other_parent(individual) for mu in individual.mating_units}
        individual_position = self._id_to_position[individual]

        ordered = list(others)
        # print(ordered)
        indices = [level.index(i) for i in ordered]
        indices = sorted(indices)

        common_parent_index = level.index(individual)

        left_of_common_parent = [i for i in indices if i < common_parent_index]
        right_of_common_parent = [i for i in indices if i > common_parent_index]
        right_of_common_parent_reversed = list(reversed(right_of_common_parent))

        # print(indices)
        # print(left_of_common_parent)
        # print(right_of_common_parent)

        for index, parent_index in enumerate(left_of_common_parent[:-1]):
            parent = level[parent_index]
            parent_position = self._id_to_position[parent]
            to_compare = level[left_of_common_parent[index + 1]]

            arch_width = individual_position.x - parent_position.x

            compare_width = individual_position.x - \
                self._id_to_position[to_compare].x + individual_position.size

            if arch_width < 2*compare_width:
                moved += self._move(
                    [parent_position], -(2*compare_width - arch_width))

        for i, parent_index in enumerate(right_of_common_parent_reversed[:-1]):
            parent = level[parent_index]
            parent_position = self._id_to_position[parent]

            to_compare = level[right_of_common_parent_reversed[i + 1]]

            arch_width = parent_position.x - individual_position.x

            compare_width = self._id_to_position[to_compare].x - \
                individual_position.x + individual_position.size

            if arch_width < 2 * compare_width:
                moved += self._move(
                    [parent_position], 2*compare_width - arch_width)

        return moved

    def _set_mates_equally_apart(self):
        moved = 0

        for level in self._individuals_by_rank:
            mating_units = self._get_mates_on_level(level)

            dual_mating_units = {(mu1, mu2) for mu1 in mating_units
                                 for mu2 in mating_units
                                 if (mu1.father is mu2.father) ^
                                    (mu1.mother is mu2.mother)}

            for mu1, mu2 in dual_mating_units:
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
                dist2 = ordered_parents[2].x - ordered_parents[1].x

                assert dist1 > 0
                assert dist2 > 0

                if dist1 < 0 or dist2 < 0 or abs(dist1 - dist2) < 1e-5:
                    return 0

                if dist1 > dist2:
                    moved += self._move(ordered_parents[2:], dist1 - dist2)
                else:
                    moved += self._move(ordered_parents[1:], dist2 - dist1)

        return moved

    def _move_overlaps(self, gap_size=8.0):
        moved = 0
        first_individual_position = self._id_to_position[
            self._individuals_by_rank[0][0]]
        min_gap = first_individual_position.size + gap_size

        for level in self._individuals_by_rank:
            level_with_positions = map(lambda i: self._id_to_position[i],
                                       level)
            for index, individual1 in enumerate(level_with_positions):
                for individual2 in level_with_positions[index+1:index+2]:
                    diff = individual2.x - individual1.x
                    if min_gap - diff > 1:
                        moved += self._move([individual2], min_gap - diff)

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

        children_center = (children[0].x + children[1].x) / 2.0

        mother = self._id_to_position[mating_unit.mother]
        father = self._id_to_position[mating_unit.father]

        parents_center = (father.x + mother.x) / 2.0

        offset = parents_center - children_center

        return self._move(children, offset)

    def _align_parents_of_children(self):
        moved = 0

        for level in reversed(self._individuals_by_rank):
            sibship_groups = self._get_sibships_on_level(level)
            for sibship in sibship_groups:
                moved += self._center_parents_of_children(sibship)

        return moved

    def _center_parents_of_children(self, sibship):
        assert len(sibship) > 0

        some_child = sibship[0]

        start_x = self._id_to_position[some_child].x
        end_x = self._id_to_position[sibship[len(sibship) - 1]].x

        children_center = (start_x + end_x) / 2.0

        mother = some_child.parents.mother
        father = some_child.parents.father

        mother_position = self._id_to_position[mother]
        father_position = self._id_to_position[father]

        ordered_parents = [mother_position, father_position]
        if mother_position.x > father_position.x:
            ordered_parents = [father_position, mother_position]

        parents_center = (mother_position.x + father_position.x) / 2.0

        offset = children_center - parents_center
        if offset > 0:
            return self._move(ordered_parents[1:], offset)
        return self._move(ordered_parents[0:1], offset)

    def _move(self, individuals, offset, already_moved=set(), min_gap=8.0):
        assert len(individuals) > 0

        if abs(offset) < 1e-5:
            return 0

        individuals = list(set(individuals) - already_moved)

        min_individual = reduce(lambda a, b: a if a.x < b.x else b,
                                individuals)
        max_individual = reduce(lambda a, b: a if a.x > b.x else b,
                                individuals)

        level = self._get_level_of_individual(min_individual.individual)

        individuals = level[level.index(min_individual.individual):
                            level.index(max_individual.individual) + 1]
        individuals = map(lambda x: self._id_to_position[x], individuals)

        individuals = list(set(individuals) - already_moved)

        if len(individuals) == 0:
            return 0

        to_move_offset = 0

        if offset > 0:
            start = min_individual.x
            end = max_individual.x
            new_end = end + offset
            to_move = {i for x in level for i in [self._id_to_position[x]]
                       if start <= i.x <= new_end}
            to_move -= already_moved
            to_move -= set(individuals)

            if to_move != set():
                to_move_offset = max(map(
                    lambda i: new_end - i.x + min_gap*2.0 + i.size,
                    to_move))
        else:
            start = min_individual.x
            end = max_individual.x
            new_start = start + offset
            to_move = {i for x in level for i in [self._id_to_position[x]]
                       if new_start <= i.x <= end}
            to_move -= already_moved
            to_move -= set(individuals)

            if to_move != set():
                to_move_offset = min(map(
                    lambda i: new_start - i.x - min_gap*2.0 - i.size,
                    to_move))

        for individual in individuals:
            individual.x += offset

        # print("moving with", offset)

        other_moved = 0
        if to_move != set():
            other_moved = self._move(
                to_move, to_move_offset, already_moved | set(individuals))

        return len(individuals) + other_moved

    @staticmethod
    def _get_mates_on_level(level):
        return {mu for i in level for mu in i.mating_units}

    def _get_first_and_last_children_positions(self, mating_unit):
        children = mating_unit.children.individuals
        children_positions = map(lambda x: self._id_to_position[x],
                                 children)
        children_positions = sorted(children_positions, key=lambda x: x.x)

        return [children_positions[0],
                children_positions[len(children_positions) - 1]]

    @staticmethod
    def _get_sibships_on_level(level):
        individuals_with_parents = filter(lambda i: bool(i.parents), level)

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

    @staticmethod
    def _generate_simple_layout(levels, level_heigh=30.0,
                                x_offset=20.0, y_offset=20.0, gap=8.0):
        result = {}
        original_x_offset = x_offset

        for rank, individuals in enumerate(levels):
            x_offset = original_x_offset
            for individual in individuals:
                position = IndividualWithCoordinates(
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
            # print(map(lambda x: x.vertex, sorted_intervals))
            result.append(map(lambda x: x.vertex, sorted_intervals))

        return result
