from dae.gene.weights import GeneWeight


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
    def get_gene_weights_query(gene_weights_config, **kwargs):
        gene_weights = kwargs.get("geneWeights", None)
        if gene_weights is None:
            return None, None, None
        if "weight" not in gene_weights:
            return None, None, None
        weights_id = gene_weights["weight"]
        if not weights_id or not hasattr(gene_weights_config, weights_id):
            return None, None, None
        range_start = gene_weights.get("rangeStart", None)
        range_end = gene_weights.get("rangeEnd", None)
        return weights_id, range_start, range_end

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
    def get_gene_syms(cls, gene_weights_config, **kwargs):
        result = cls.get_gene_symbols(**kwargs) | cls.get_gene_weights(
            gene_weights_config, **kwargs
        )

        return result if result else None

    @classmethod
    def get_gene_weights(cls, gene_weights_config, **kwargs):
        weights_id, range_start, range_end = cls.get_gene_weights_query(
            gene_weights_config, **kwargs
        )

        if weights_id is None:
            return set([])

        weights = GeneWeight(
            weights_id, getattr(gene_weights_config, weights_id)
        )
        return weights.get_genes(wmin=range_start, wmax=range_end)
