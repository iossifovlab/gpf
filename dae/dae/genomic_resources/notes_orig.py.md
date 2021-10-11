from typing import Any, List, Dict, Set, Type, Iterator, Tuple

class GenomicResrouceException(Exception):
    pass

class GenomicResource:
    pass

class PositionScoreResource(GenomicResource):
    # Lubo's starting point
    def load(): pass
    def fetch_scores(chrom,positions : List[int], scores : List[str]) : pass
    def fetch_scores_range(chrom,pos_begin : int,pos_end : int, scores : List[str]): pass
    def fetch_scores_range_agg(chrom,pos_begin : int,pos_end : int, scores : List[str], agg_fun): pass

    # Updated version
    def open(): pass
    def close(): pass

    def get_all_scores() -> List[str]: pass
    def get_default_scores() -> List[str]: pass
    def get_score_types() -> Dict[str,Type]: pass

    def get_all_chromosomes() -> List[str]: pass

    def get_reference_genome_build() -> str: 
        # returns something like "hg38" or "hg19" ...
        # One way to implement that is to move the function to the GenomicResoruce class 
        # and to return the value of self.get_id().split("/")[0]
        pass


    def fetch_scores(chrom : str, positions : List[int], are_position_sorted : bool = False, 
                     scores : Set[str] = None) -> Iterator[Tuple[int,Dict[str,Any]]]: 
        '''
            positions are 1-based!

            assert chrom in get_all_chromosomes()
            
            Notes: 
                The returned iterator will return elements of 
                    (position_1,{score_1:v_11, score_2:v_12, ...}, 
                    (position_2, ...))
                with the positions in ascending order, and duplicates positions removed.
                Not all positions will be returned. Positions for which the resouce has not available
                data can be skipped. For example:
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
        pass

    def fetch_scores_range(chrom : str, pos_begin : int, pos_end : int, 
                           scores : Set[str] = None) -> Iterator[Tuple[int,Dict[str,Any]]]: 
        '''
            assert pos_begin < pos_end
            It will return positions [pos_begin,  pos_end) but positions can be skipped.
            See above for more details.
        '''
        pass

    def fetch_scores_range_agg(chrom : str, pos_begin : int, pos_end : int, 
            scores : List[str], agg_fun) -> Dict[str,Any]]]: 
        '''
        '''
        pass

    # 3. How do we represent missing values
    #   OK
    # 1. It seem returning an iterator is better
    #      OK
    # 2. Can we consider differnt value types: int, float, bool, str
    #      OK
    # 4. Is it more oppropriate to open and close within any function
    #     We seem to agree that open close at resource level is better.

class PositionScoreAnnotator:
    def __init__(self):
        self.positionScoreResource = None
        self.scores = []
        self.attributes = []

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

    def annotate_allele(self,allele):
        '''
            a is a SummaryAllel
        '''
        if allele.is_substitution():
            R = self.positionScoreResource.fetch_score(allele.chrom,allele.pos,self.scores)
            if R:
                for a,s in zip(self.attributes,self.scores):
                    allele.set_atts(a,R[s])
        else:
            if allele.is_indel():
                fP = allele.pos-1
                lP = allele.pos+len(allele.ref)
            elif allele.is_cnv():
                fP = allele.pos
                lP = allele.posEnd
            else:
                raise Exception()

            scoresBuff = {s:at() for s,at in zip(self.scores,self.aggregateType)}
            R = self.positionScoreResource.fetch_scores_agg(allele.chrom,fP,lP,scoresBuff)
            if R:
                for a,s in zip(self.attributes,self.scores):
                    allele.set_atts(a,R[s])


class AbstractAggregatorObject:
    def add(v): pass
    def get_final(): pass

class MaxAggregator(AbstractAggregatorObject):
    def __init__(ma):
        ma.cM = None

    def add(ma,v):
        if ma.cM and v:
            ma.cM = max(ma.cM,v)
        elif v:
            ma.cM = v

    def get_final(ma):
        return ma.cM


class MeanAggregator(AbstractAggregatorObject):
    def __init__(ma):
        ma.sm = 0
        ma.n = 0

    def add(ma,v):
        if v:
            ma.sm += v
            ma.n += 1

    def get_final(ma):
        if ma.n:
            return float(ma.sm)/ma.n
        return None

# 
def max_agg(current,next):
    if current:
        return max(current,next)
    return next

    def stop(self):
        self.positionScoreResource.close()




class PositionScoreResrouce:
    def fetch_scores(chrom : str, position : int, scores : List[str]) -> Dict[str,Any]: pass
    def fetch_scores_agg(chrom : str, pos_begin : int, pos_end: int, 
                         scoresAggregators : Dict[str,AbstractAggregatorType]) -> Dict[str,Any]: pass

class NPScoreResource:

    def fetch_scores(chrom : str, position : int, nt : str, scores : List[str]) -> Dict[str,Any]: pass

    # The aggregator to be used to aggregate scores accross nucleotides at the position
    def fetch_scores_ntAgg(chrom : str, position : int, scores : Dict[str,AbstractAggregatorType]) -> Dict[str,Any]: pass

    # The first aggregator type will be used to aggregate scores accross nucleotides at each position.
    # The second  aggregator type will be used to aggregate scores accross position.
    def fetch_scores_agg(chrom : str, pos_begin : int, pos_end: int, 
                        scores : Dict[str,Tuple[AbstractAggregatorType,AbstractAggregatorType]]) -> Dict[str,Any]: pass
