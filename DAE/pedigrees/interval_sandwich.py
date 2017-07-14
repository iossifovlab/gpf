class Interval:

    def __init__(self, left=1, right=1):
        self.left = left
        self.right = right


class IntervalForVertex(Interval):

    def __init__(self, vertex, left=1, right=1):
        super().__init__(left, right)
        self.vertex = vertex


class Realization:
    def __init__(self, graph, forbidden_graph, intervals=[], domain=[],
                 max_width=3):
        self.graph = graph
        self.forbidden_graph = forbidden_graph
        self.intervals = intervals
        self.domain = domain
        self.max_width = max_width

    def __repr__(self):
        ordered_domain = sorted([repr(v) for v in self.domain])
        return ";".join(ordered_domain)

    def extend(self, vertex):
        if not self.can_extend(vertex):
            return False

        max_right = [self.get_interval(v).right
                     for v in self.get_maximal_set()]

        p = 0.5 + max_right

        for active_vertex in self.get_active_vertices():
            interval = self.get_interval(active_vertex)
            interval.right = p + 1

        self.domain.push(vertex)
        self.intervals.push(IntervalForVertex(vertex, p, p + 1))

        return True

    def can_extend(self, new_vertex):
        temp_realization = Realization(
            self.graph,
            self.forbidden_graph,
            self.intervals + [IntervalForVertex(new_vertex)],
            self.domain + [new_vertex]
        )

        if temp_realization._exceeds_max_width():
            return False

        if not self._old_dangling_same(new_vertex, temp_realization):
            return False

        if not self._new_dangling_valid(new_vertex, temp_realization):
            return False

        if not self._new_active_valid(new_vertex, temp_realization):
            return False

        if self._has_forbidden_edge(new_vertex):
            return False

        return True

    def _exceeds_max_width(self):
        return len(self.get_active_vertices) >= self.max_width

    def _has_forbidden_edge(self, new_vertex):
        forbidden = self.forbidden_graph.neighbours(new_vertex)
        active_vertices = self.get_active_vertices()

        return len(forbidden - active_vertices) != 0

    def _new_active_valid(self, new_vertex, new_realization):
        new_active = new_realization.get_active_vertices()
        new_active_without_dangling = \
            {v for v in new_active
                if len(new_realization.dangling(v)) != 0}

        return new_active == new_active_without_dangling

    def _new_dangling_valid(self, new_vertex, new_realization):
        new_dangling = new_realization.dangling(new_vertex)
        new_edges = set(self.graph.neighbours(new_vertex)) - \
            self.get_active_vertices()
        return new_dangling == new_edges

    def _old_dangling_same(self, new_vertex, new_realization):
        for active_vertex in self.get_active_vertices():
            dangling = self.dangling(active_vertex)
            new_dangling = new_realization.dangling(active_vertex)
            new_dangling.add(new_vertex)

            if len(dangling - new_dangling) != 0:
                return False

        return True

    def get_interval(self, vertex):
        index = self.domain.index(vertex)

        return self.intervals[index]

    def is_in_interval_order(self, v1, v2):
        intervalV1 = self.get_interval(v1)
        intervalV2 = self.get_interval(v2)

        if not intervalV1 or not intervalV2:
            return False

        return intervalV1.right < intervalV2.left

    def is_maximal(self, vertex):
        return all([v is not vertex and self.is_in_interval_order(vertex, v)
                    for v in self.domain])

    def get_maximal_set(self):
        return {v for v in self.domain if self.is_maximal(v)}

    def get_active_vertex_edges(self, vertex):
        return set(self.graph.neighbours(vertex)).difference(self.domain)

    def is_active_vertex(self, vertex):
        neighbours = set(self.graph.neighbours(vertex))
        return len(neighbours.difference(self.domain)) != 0

    def get_active_vertices(self, vertex):
        return {v for v in self.domain if self.is_active_vertex(v)}

    def dangling(self, vertex):
        return self.get_active_vertex_edges(vertex)


class SandwichInstance:
    def __init__(self, vertices, required_graph, forbidden_graph):
        self.vertices = vertices
        self.required_graph = required_graph
        self.forbidden_graph = forbidden_graph
