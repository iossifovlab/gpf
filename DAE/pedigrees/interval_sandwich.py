import networkx as nx
import itertools
from collections import deque
import copy
import pprint


class Interval(object):

    def __init__(self, left=0.0, right=1.0):
        self.left = left
        self.right = right


class IntervalForVertex(Interval):

    def __init__(self, vertex, left=0.0, right=1.0):
        super(IntervalForVertex, self).__init__(left, right)
        self.vertex = vertex

    def __repr__(self):
        return "i[{}> {}:{}]".format(self.vertex, self.left, self.right)


class Realization:
    def __init__(self, graph, forbidden_graph, intervals=None, domain=None,
                 max_width=3):
        if domain is None:
            domain = []
        if intervals is None:
            intervals = []
        self.graph = graph
        self.forbidden_graph = forbidden_graph
        self.intervals = intervals
        self.domain = domain
        self.max_width = max_width

    def copy(self):
        return Realization(
            self.graph, self.forbidden_graph,
            map(copy.copy, self.intervals),
            copy.copy(self.domain),
            self.max_width
        )

    def __repr__(self):
        ordered_domain = sorted([repr(v) for v in self.domain])
        return ";".join(ordered_domain)

    def extend(self, vertex):

        if not self.can_extend(vertex):
            return False

        max_right = next(self.get_interval(v).right
                         for v in self.get_maximal_set())

        p = 0.5 + max_right

        for active_vertex in self.get_active_vertices():
            interval = self.get_interval(active_vertex)
            interval.right = p + 1

        self.domain.append(vertex)
        self.intervals.append(IntervalForVertex(vertex, p, p + 1))

        return True

    def can_extend(self, new_vertex):
        temp_realization = Realization(
            self.graph,
            self.forbidden_graph,
            self.intervals + [IntervalForVertex(new_vertex)],
            self.domain + [new_vertex]
        )

        if temp_realization._exceeds_max_width():
            # print("max width reached!")
            return False

        if self._has_forbidden_edge(new_vertex):
            # print("_has_forbidden_edge!")
            return False

        if not self._old_dangling_same(new_vertex, temp_realization):
            # print("_old_dangling_same!")
            return False

        if not self._new_dangling_valid(new_vertex, temp_realization):
            # print("_new_dangling_valid!")
            return False

        if not self._new_active_valid(new_vertex, temp_realization):
            # print("_new_active_valid!")
            return False

        return True

    def _exceeds_max_width(self):
        return len(self.get_active_vertices()) >= self.max_width

    def _has_forbidden_edge(self, new_vertex):
        forbidden = set(self.forbidden_graph.neighbors(new_vertex))
        active_vertices = self.get_active_vertices()

        return forbidden & active_vertices != set()

    def _new_active_valid(self, new_vertex, new_realization):
        new_active = new_realization.get_active_vertices()
        old_active_and_new_vertex = self.get_active_vertices() | {new_vertex}
        expected_new_active = \
            {v for v in old_active_and_new_vertex
                if len(new_realization.dangling(v)) != 0}

        return new_active == expected_new_active

    def _new_dangling_valid(self, new_vertex, new_realization):
        new_dangling = new_realization.dangling(new_vertex)
        new_edges = set(self.graph.neighbors(new_vertex)) - \
            self.get_active_vertices()
        return new_dangling == new_edges

    def _old_dangling_same(self, new_vertex, new_realization):
        for active_vertex in self.get_active_vertices():
            dangling = self.dangling(active_vertex)
            new_dangling = new_realization.dangling(active_vertex)
            dangling -= {new_vertex}

            if new_dangling != dangling:
                return False

        return True

    def get_interval(self, vertex):
        index = self.domain.index(vertex)

        return self.intervals[index]

    def is_in_interval_order(self, v1, v2):
        interval1 = self.get_interval(v1)
        interval2 = self.get_interval(v2)

        if not interval1 or not interval2:
            return False

        return interval1.right < interval2.left

    def is_maximal(self, vertex):
        is_maximal = [v is vertex or not self.is_in_interval_order(vertex, v)
                      for v in self.domain]
        return all(is_maximal)

    def get_maximal_set(self):
        return {v for v in self.domain if self.is_maximal(v)}

    def get_active_vertex_edges(self, vertex):
        return set(self.graph.neighbors(vertex)).difference(self.domain)

    def is_active_vertex(self, vertex):
        neighbors = set(self.graph.neighbors(vertex))
        return len(neighbors.difference(self.domain)) != 0

    def get_active_vertices(self):
        return {v for v in self.domain if self.is_active_vertex(v)}

    def dangling(self, vertex):
        return self.get_active_vertex_edges(vertex)


class SandwichInstance:
    def __init__(self, vertices, required_graph, forbidden_graph):
        self.vertices = vertices
        self.required_graph = required_graph
        self.forbidden_graph = forbidden_graph

    @staticmethod
    def from_sets(all_vertices, required_set, forbidden_set):
        required_graph = nx.Graph()
        required_graph.add_nodes_from(all_vertices)
        required_graph.add_edges_from(required_set)

        forbidden_graph = nx.Graph()
        forbidden_graph.add_nodes_from(all_vertices)
        forbidden_graph.add_edges_from(forbidden_set)

        return SandwichInstance(all_vertices, required_graph, forbidden_graph)


def copy_graph(g):
    result = nx.Graph()
    result.add_nodes_from(g.nodes())
    result.add_edges_from(g.edges())

    return result


class SandwichSolver(object):

    @staticmethod
    def solve(sandwich_instance):
        forbidden_graph = sandwich_instance.forbidden_graph
        # print("all forbidden:", len(forbidden_graph.edges()))
        # pprint.pprint(forbidden_graph.edges())
        # print("all required:", len(sandwich_instance.required_graph.edges()))
        # pprint.pprint(sandwich_instance.required_graph.edges())
        # print("common:")
        # pprint.pprint(set(sandwich_instance.required_graph.edges()) &
        #               set(sandwich_instance.forbidden_graph.edges()))
        for count in range(0, len(forbidden_graph.edges())):
            for edges_to_remove in itertools.combinations(
                    sorted(forbidden_graph.edges()),
                    count):
                # if count == 2:
                #     return

                # print("removing", edges_to_remove)

                current_forbidden_graph = copy_graph(forbidden_graph)
                current_forbidden_graph.remove_edges_from(edges_to_remove)

                current_instance = SandwichInstance(
                    sandwich_instance.vertices,
                    sandwich_instance.required_graph,
                    current_forbidden_graph)

                result = SandwichSolver.try_solve(current_instance)
                if result:
                    print("removed:", count)  # , edges_to_remove)
                    return result


    @staticmethod
    def try_solve(sandwich_instance):
        initial_realization = []
        current_iteration = 0

        for vertex in sandwich_instance.vertices:
            initial_realization.append(
                Realization(
                    sandwich_instance.required_graph,
                    sandwich_instance.forbidden_graph,
                    [IntervalForVertex(vertex)],
                    [vertex]
                )
            )
        realizations_queue = deque(sorted(initial_realization, key=str))

        visited_realizations = {}

        vertices_length = len(sandwich_instance.vertices)
        # print(realizations_queue)

        while len(realizations_queue) > 0:
            realization = realizations_queue.pop()
            current_iteration += 1

            if current_iteration == 10000:
                print("exit ot 10k it")
                return None

            other_vertices = sandwich_instance.vertices \
                .difference(realization.domain)

            other_vertices = sorted(other_vertices, key=str)

            for vertex in other_vertices:
                cloned_realization = realization.copy()

                extended = cloned_realization.extend(vertex)

                if not extended:
                    continue

                if len(cloned_realization.domain) == vertices_length:
                    return cloned_realization.intervals
                else:
                    domain_string = repr(cloned_realization)
                    if domain_string not in visited_realizations:
                        visited_realizations[domain_string] = True
                        realizations_queue.append(cloned_realization)

        return None
