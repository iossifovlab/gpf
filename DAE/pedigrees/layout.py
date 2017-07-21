from collections import defaultdict


class PedigreeMemberWithCoordinates:

    def __init__(self, member, x=0, y=0, size=21, scale=1.0):
        self.member = member
        self.x = x
        self.y = y
        self.size = size
        self.scale = scale


class Line:

    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2


class Layout:

    def __init__(self):
        self.members = []
        self.lines = []

    @staticmethod
    def generate_from_intervals(intervals):
        individuals_by_rank = Layout._intervals_by_ranks(intervals)
        # for rank in individuals_by_rank:
        #     print(rank)

    @staticmethod
    def _intervals_by_ranks(intervals):
        result = []

        rank_to_individuals = defaultdict(list)
        for interval in intervals:
            rank_to_individuals[interval.vertex.rank].append(interval)

        for key in sorted(rank_to_individuals.keys()):
            sorted_intervals = sorted(rank_to_individuals[key],
                                      key=lambda x: (x.left, x.right))
            result.append(map(lambda x: x.vertex, sorted_intervals))

        return result
