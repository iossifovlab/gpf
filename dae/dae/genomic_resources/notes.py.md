from typing import List, Any, Dict, Optional


class AbstractAggregator:
    def add(v): pass
    def get_final(): pass

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
    pass


class GenomicScoreResource:
    pass


class PositionScoreResource(GenomicScoreResource):

    '''
        positions are 1-based!

        assert chrom in get_all_chromosomes()

        Notes: 
            The returned iterator will return elements of 
                (position_1,{score_1:v_11, score_2:v_12, ...}, 
                (position_2, ...))
            with the positions in ascending order, and duplicates positions removed.
            Not all positions will be returned. Positions for which the resouce 
            has not available data can be skipped. For example:
                - chrom is not covered [RAISE AN EXCEPTION!]
                    the resouce doesn't cover chrY
                    the resource doesn't cover the weird extra haplotypes
                    chrom is completely off, outside of the reference genome, idicative of a bug
                - a given position is 0 or less [RAISE AN EXCEPATION!]
                - a given positions is  larger than the length of the chromosome [SKIP POSITION]
                - a given positions falls into a region not covered by the resource: [SKIP POSITION]
                    centromeres, telomeres, ...
                    poor multiple alignment region,
                    repetetive region, 

            Missing values will be represented by None. The type of the values will be 
            consistenet with what get_score_types returns.

        scores:
            If None, the function will return values for all scores (as returned by get_all_scores())

        are_positions_sorted:
            Frequently, it is more efficient to work if the positions are sorted in increasing order. 
            If are_positions_sorted is True, the function assumes that the positions are indeed in sorted order.
            If are_positions_sorted is False, the function will first sort the positions. In both cases, the results
            will be returned in the sorted order.

    '''

    # Updated version
    def open(): pass
    def close(): pass

    def get_all_scores() -> List[str]: pass
    def get_default_scores() -> List[str]: pass
    def get_score_types() -> Dict[str, Type]: pass

    def get_all_chromosomes() -> List[str]: pass

    def fetch_scores(
            chrom: str, position: int, scores: List[str] = None) -> Optional[Dict[str, Any]]:

        pass

    def fetch_scores_agg(
            chrom: str, pos_begin: int, pos_end: int,
            scoresAggregators: Dict[str, type(AbstractAggregator)]) -> Optional[Dict[str, Any]]:

        aggregators = {
            sc: aggr() for sc, aggr in scoresAggregators.items()
        }
        # ...

        return {
            sc: aggr.get_final() for sc, aggr in aggregators.items()
        }
        pass


class NPScoreResource(GenomicScoreResource):

    def fetch_scores(
        chrom: str, position: int, nt: str, scores: List[str] = None) -> Dict[str, Any]: pass

    # The first aggregator type will be used to aggregate scores accross nucleotides at each position.
    # The second  aggregator type will be used to aggregate scores accross position.
    def fetch_scores_agg(
        chrom: str, pos_begin: int, pos_end: int,
        scores: Dict[
            str, Tuple[
                type(AbstractAggregator),
                type(AbstractAggregator)]]) -> Dict[str, Any]: pass


class NPScoreResource(GenomicScoreResource):

    def fetch_scores(
        chrom: str, position: int, ref: str, alt: str,
        scores: List[str] = None) -> Dict[str, Any]: pass


DEFAULT_AGGREGATIONS = {
    str: ConcatAggregator,
    float: MaxAggregator,
    int: MaxAggregator,
}


class PositionScoreAnnotator:
    def __init__(self):
        self.positionScoreResource = None
        self.scores = []
        self.attributes_mapping = []

        self.aggregateType = []

        '''
        # A: annotation level aggregator types
        #    value type -> aggregator
        #    score name -> aggregator
        #
        # B: resource level aggregator types
        #    value type -> aggregator
        #    score name -> aggregator
        #
        # C: default type aggregator types
        #    float -> max
        #    int -> max
        #    string -> concatenate
               

        for scores in self.scores:
            check A,B,C in order if the scores is explicitly meentioned
            check A,B,C in order if the type of the score is configured
            return the first match.
            C should cover all the types.

        '''

    def start(self):
        self.positionScoreResource.open()

    def annotate_allele(self, allele, context):
        '''
            a is a SummaryAllel
        '''
        if allele.is_substitution():
            R = self.positionScoreResource.fetch_score(
                allele.chrom, allele.pos, self.scores)
            if R:
                for a, s in zip(self.attributes, self.scores):
                    allele.set_atts(a, R[s])
        else:
            if allele.is_indel():
                fP = allele.pos-1
                lP = allele.pos+len(allele.ref)
            elif allele.is_cnv():
                fP = allele.pos
                lP = allele.posEnd
            else:
                raise Exception()

            scoresBuff = {s: at()
                          for s, at in zip(self.scores, self.aggregateType)}
            R = self.positionScoreResource.fetch_scores_agg(
                allele.chrom, fP, lP, scoresBuff)
            if R:
                for a, s in zip(self.attributes, self.scores):
                    allele.set_atts(a, R[s])
