from GeneTerms import GeneTerms
class GeneTerm:
	def __init__(self, geneTerms):
		self.tDesc = geneTerms.tDesc
		self.geneNS = geneTerms.geneNS
		self.t2G = dict([(key,dict(val)) for key,val in geneTerms.t2G.items()])
		self.g2T = dict([(key, dict(val)) for key, val in geneTerms.g2T.items()])


