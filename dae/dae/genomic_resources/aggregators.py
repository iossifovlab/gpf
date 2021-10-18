class AbstractAggregator:
    def __call__(self):
        return self.get_final()

    def add(self, v):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def get_final(self):
        raise NotImplementedError()


class MaxAggregator(AbstractAggregator):
    def __init__(self):
        self.current_max = None

    def add(self, v):
        if self.current_max is not None and v is not None:
            self.current_max = max(self.current_max, v)
        elif v is not None:
            self.current_max = v

    def clear(self):
        self.current_max = None

    def get_final(self):
        return self.current_max


class MinAggregator(AbstractAggregator):
    def __init__(self):
        self.current_min = None

    def add(self, v):
        if self.current_min is not None and v is not None:
            self.current_min = min(self.current_min, v)
        elif v is not None:
            self.current_min = v

    def clear(self):
        self.current_min = None

    def get_final(self):
        return self.current_min


class MeanAggregator(AbstractAggregator):
    def __init__(self):
        self.sum = 0
        self.count = 0

    def add(self, v):
        if v is not None:
            self.sum += v
            self.count += 1

    def clear(self):
        self.sum = 0
        self.count = 0

    def get_final(self):
        if self.count:
            return self.sum / self.count
        return None


class ConcatAggregator(AbstractAggregator):
    def __init__(self):
        self.out = ""

    def add(self, v):
        if v:
            self.out += v

    def clear(self):
        self.out = ""

    def get_final(self):
        if self.out == "":
            return None

        return self.out
