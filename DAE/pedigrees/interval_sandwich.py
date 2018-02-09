import networkx as nx
import itertools
from collections import deque
import copy


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


class Realization(object):
    def __init__(self, graph, forbidden_graph, intervals=None, domain=None,
                 max_width=3, _cached_active_vertices=None,
                 _cached_maximal_set=None, _graph_neighbors_cache=None):
        if domain is None:
            domain = []
        if intervals is None:
            intervals = []
        self.graph = graph
        self.forbidden_graph = forbidden_graph
        self.intervals = intervals
        self.domain = domain
        self.max_width = max_width
        self._cached_active_vertices = _cached_active_vertices
        self._cached_maximal_set = _cached_maximal_set

        if _graph_neighbors_cache is None:
            print "_graph_neighbors_cache recomputed"
            _graph_neighbors_cache = {
                v: set(self.graph.neighbors(v))
                for v in self.graph.nodes()
            }

        self._graph_neighbors_cache = _graph_neighbors_cache

    def copy(self):
        return Realization(
            self.graph, self.forbidden_graph,
            map(copy.copy, self.intervals),
            copy.copy(self.domain),
            self.max_width,
            self._cached_active_vertices,
            self._cached_maximal_set,
            self._graph_neighbors_cache
        )

    def __repr__(self):
        ordered_domain = sorted([repr(v) for v in self.domain])
        return ";".join(ordered_domain)

    def extend(self, vertex):

        if not self.can_extend(vertex):
            return False

        self.force_extend(vertex)

        return True

    def force_extend(self, vertex):

        max_right = next(self.get_interval(v).right
                         for v in self.get_maximal_set())

        p = 0.5 + max_right

        for active_vertex in self.get_active_vertices():
            interval = self.get_interval(active_vertex)
            interval.right = p + 1

        self.domain.append(vertex)
        self.intervals.append(IntervalForVertex(vertex, p, p + 1))

        self._cached_active_vertices = None
        self._cached_maximal_set = None

    def can_extend(self, new_vertex):
        temp_realization = Realization(
            self.graph,
            self.forbidden_graph,
            self.intervals + [IntervalForVertex(new_vertex)],
            self.domain + [new_vertex],
            _graph_neighbors_cache=self._graph_neighbors_cache
        )

        if self._has_forbidden_edge(new_vertex):
            # print("_has_forbidden_edge!")
            return False

        if temp_realization._exceeds_max_width():
            # print("max width reached!")
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

    def is_in_interval_order(self, v1_idx, v2_idx):
        # interval1 = self.get_interval(v1)
        # interval2 = self.get_interval(v2)

        # if (v1_idx < 0 or v1_idx >= len(self.domain) or
        #         v2_idx < 0 or v2_idx >= len(self.domain)):
        #     return False

        interval1 = self.intervals[v1_idx]
        interval2 = self.intervals[v2_idx]

        return interval1.right < interval2.left

    def is_maximal(self, index):
        for i, v in enumerate(self.domain):
            if i != index and self.is_in_interval_order(index, i):
                return False

        return True
        # return all(i == index or not self.is_in_interval_order(index, i)
        #            for i, v in enumerate(self.domain))

    def get_maximal_set(self):
        if self._cached_maximal_set:
            return self._cached_maximal_set

        self._cached_maximal_set = {
            v for i, v in enumerate(self.domain) if self.is_maximal(i)}

        return self._cached_maximal_set

    def get_active_vertex_edges(self, vertex):
        return self._graph_neighbors_cache[vertex].difference(self.domain)

    def is_active_vertex(self, vertex):
        neighbors = self._graph_neighbors_cache[vertex] # set(self.graph.neighbors(vertex))

        for v in neighbors:
            if v not in self.domain:
                return True

        return False

    def get_active_vertices(self):
        if self._cached_active_vertices:
            return self._cached_active_vertices

        self._cached_active_vertices = set()
        for v in self.domain:
            if self.is_active_vertex(v):
                self._cached_active_vertices.add(v)

        # self._cached_active_vertices = {
        #     v for v in self.domain if self.is_active_vertex(v)}

        return self._cached_active_vertices

    def dangling(self, vertex):
        return self.get_active_vertex_edges(vertex)


class SandwichInstance(object):
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

                print("removing", edges_to_remove)

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

        for i, vertex in enumerate(sandwich_instance.vertices):
            initial_realization.append(
                Realization(
                    sandwich_instance.required_graph,
                    sandwich_instance.forbidden_graph,
                    [IntervalForVertex(vertex)],
                    [vertex],
                    _graph_neighbors_cache=initial_realization[0]._graph_neighbors_cache if i > 0 else None
                )
            )

        realizations_queue = deque(sorted(initial_realization, key=str))

        visited_realizations = {}

        vertices_length = len(sandwich_instance.vertices)
        # print(realizations_queue)

        while len(realizations_queue) > 0:
            realization = realizations_queue.pop()
            current_iteration += 1

            # if current_iteration == 100000:
            #     print("Bailing at {} iterations...".format(current_iteration))
            #     return None

            other_vertices = sandwich_instance.vertices \
                .difference(realization.domain)

            can_extend_f = realization.can_extend

            for vertex in other_vertices:
                # cloned_realization = realization.copy()

                can_extend = can_extend_f(vertex)

                if not can_extend:
                    continue

                cloned_realization = realization.copy()
                cloned_realization.force_extend(vertex)

                if len(cloned_realization.domain) == vertices_length:
                    print("iterations count", current_iteration)
                    return cloned_realization.intervals
                else:
                    domain_string = repr(cloned_realization)
                    if domain_string not in visited_realizations:
                        visited_realizations[domain_string] = True
                        realizations_queue.append(cloned_realization)

        return None
