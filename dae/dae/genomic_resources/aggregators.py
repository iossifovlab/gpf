class AbstractAggregator:
    def add(v):
        pass

    def get_final():
        pass

    def __call__(self):
        return self.get_final()


class MaxAggregator(AbstractAggregator):
    def __init__(self):
        self.cM = None

    def add(self, v):
        if self.cM and v:
            self.cM = max(self.cM, v)
        elif v:
            self.cM = v

    def get_final(self):
        return self.cM


class MeanAggregator(AbstractAggregator):
    def __init__(self):
        self.sm = 0
        self.n = 0

    def add(self, v):
        if v:
            self.sm += v
            self.n += 1

    def get_final(self):
        if self.n:
            return float(self.sm)/self.n
        return None


class ConcatAggregator(AbstractAggregator):
    def __init__(self):
        self.out = ""

    def add(self, v):
        if v:
            self.out += v

    def get_final(self):
        if self.out == "":
            return None

        return self.out
