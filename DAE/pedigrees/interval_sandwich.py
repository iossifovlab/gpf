class Interval:

    def __init__(self, left=1, right=1):
        self.left = left
        self.right = right


class IntervalForVertex(Interval):

    def __init__(self, vertex, left=1, right=1):
        super().__init__(left, right)
        self.vertex = vertex


class Realization:
    def __init__(self, graph, forbidden_graph, intervals=[], domain=[]):
        self.graph = graph
        self.forbidden_graph = forbidden_graph
        self.intervals = intervals
        self.domain = domain

    def __repr__(self):
        ordered_domain = sorted([repr(v) for v in self.domain])
        return ";".join(ordered_domain)

    def extend(self, vertex):
        if not self.can_extend(vertex):
            return False

        max_right = [self.get_interval(v).right
                     for v in self.get_maximal_set()]

        p = 0.5 + max_right

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

    def get_active_vertices(self):
