
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
