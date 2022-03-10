from dae.gene.gene_scores import GeneScore


class GeneSymsMixin(object):
    @staticmethod
    def get_gene_symbols(**kwargs):
        gene_symbols = kwargs.get("geneSymbols", None)
        if gene_symbols is None:
            return set([])

        if isinstance(gene_symbols, str):
            gene_symbols = gene_symbols.replace(",", " ")
            gene_symbols = gene_symbols.split()

        return set([g.strip() for g in gene_symbols])

    @staticmethod
    def get_gene_scores_query(gene_scores_config, **kwargs):
        gene_scores = kwargs.get("geneScores", None)
        if gene_scores is None:
            return None, None, None
        if "score" not in gene_scores:
            return None, None, None
        scores_id = gene_scores["score"]
        if not scores_id or not hasattr(gene_scores_config, scores_id):
            return None, None, None
        range_start = gene_scores.get("rangeStart", None)
        range_end = gene_scores.get("rangeEnd", None)
        return scores_id, range_start, range_end

    @staticmethod
    def get_gene_set_query(**kwargs):
        query = kwargs.get("geneSet", None)
        if query is None:
            return None, None, None
        if "geneSet" not in query or "geneSetsCollection" not in query:
            return None, None, None
        gene_sets_collection = query["geneSetsCollection"]
        gene_set = query["geneSet"]
        if not gene_sets_collection or not gene_set:
            return None, None, None
        gene_sets_types = query.get("geneSetsTypes", [])
        return gene_sets_collection, gene_set, gene_sets_types

    @classmethod
    def get_gene_syms(cls, gene_scores_config, **kwargs):
        result = cls.get_gene_symbols(**kwargs) | cls.get_gene_scores(
            gene_scores_config, **kwargs
        )

        return result if result else None

    @classmethod
    def get_gene_scores(cls, gene_scores_config, **kwargs):
        scores_id, range_start, range_end = cls.get_gene_scores_query(
            gene_scores_config, **kwargs
        )

        if scores_id is None:
            return set([])

        scores = GeneScore(
            scores_id, getattr(gene_scores_config, scores_id)
        )
        return scores.get_genes(wmin=range_start, wmax=range_end)
