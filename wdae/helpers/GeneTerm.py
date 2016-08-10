import itertools


def ddunion(dd1, dd2):
    dds = [dd1, dd2]
    items = map(lambda d: list(d.items()), dds)
    res = {}
    for (k, v) in itertools.chain(*items):
        res.setdefault(k, dict()).update(v)
    return res


class GeneTerm:

    def __init__(self, geneTerms, geneSetName=None):
        if geneSetName is None:
            self.tDesc = geneTerms.tDesc
            self.geneNS = geneTerms.geneNS
            self.t2G = dict([(key, dict(val))
                             for key, val in geneTerms.t2G.items()])
            self.g2T = dict([(key, dict(val))
                             for key, val in geneTerms.g2T.items()])
        else:
            self.tDesc = dict([(geneSetName, geneTerms.tDesc[geneSetName])])
            self.geneNS = geneTerms.geneNS
            self.t2G = dict([(geneSetName, geneTerms.t2G[geneSetName])])
            self.g2T = dict([(key, dict([(gt, d) for (gt, d) in val.items()
                                         if gt == geneSetName]))
                             for key, val in geneTerms.g2T.items()
                             if geneSetName in val])

    def union(self, gt):
        self.tDesc.update(gt.tDesc)
        self.t2G = ddunion(self.t2G, gt.t2G)
        self.g2T = ddunion(self.g2T, gt.g2T)
