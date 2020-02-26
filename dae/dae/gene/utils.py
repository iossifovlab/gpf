import sys
from copy import deepcopy
from box import Box

from dae.gene.gene_term import loadGeneTerm


def rename_gene_terms(config, gene_terms, inNS):
    assert {gene_terms.geneNS, inNS} <= {'id', 'sym'}, \
        (f'The provided namespaces "{gene_terms.geneNS}",'
         ' "{inNS}" must be either "id" or "sym"!')

    result = deepcopy(gene_terms)

    if result.geneNS == inNS:
        return result
    elif result.geneNS == 'id' and inNS == 'sym':
        def rF(x):
            genes = getGenes(config.gene_info)
            if x in genes:
                return genes[x].sym
        result.renameGenes('sym', rF)
    elif result.geneNS == 'sym' and inNS == 'id':
        result.renameGenes(
            'id',
            lambda x: getCleanGeneId(config.gene_info, 'sym', x)
        )
    return result


def getGeneTermAtt(config, gt_id, attName):
    gene_term = getattr(config.gene_terms, gt_id)
    return getattr(gene_term, attName)


def getGeneTerms(config, gt_id='main', inNS='sym'):
    fl = getattr(config.gene_terms, gt_id).file
    gt = loadGeneTerm(fl)
    try:
        gt = rename_gene_terms(config, gt, inNS)
    except AssertionError:
        raise Exception(
            (f'Unknown namespace(s) for the {gt_id} gene terms:'
             ' |{gt.geneNS}| -> |{inNS}|')
        )
    return gt


def _parseNCBIGeneInfo(config):
    genes = {}
    nsTokens = {}
    with open(config.gene_info_file) as f:
        for line in f:
            if line[0] == "#":
                # print "COMMENT: ", line
                continue
            cs = line.strip().split("\t")
            if len(cs) != 15:
                raise Exception(
                    'Unexpected line in the ' + config.gene_info_file)

            # Format: tax_id GeneID Symbol LocusTag Synonyms dbXrefs
            # chromosome map_location description
            # type_of_gene Symbol_from_nomenclature_authority
            # Full_name_from_nomenclature_authority Nomenclature_status
            # Other_designations Modification_date
            # (tab is used as a separator, pound sign - start of a comment)
            (tax_id, GeneID, Symbol, LocusTag, Synonyms, dbXrefs,
                chromosome, map_location, description, type_of_gene,
                Symbol_from_nomenclature_authority,
                Full_name_from_nomenclature_authority, Nomenclature_status,
                Other_designations, Modification_date) = cs

            gi = Box()
            gi.id = GeneID
            gi.sym = Symbol
            gi.syns = set(Synonyms.split("|"))
            gi.desc = description

            if (gi.id in genes):
                raise Exception(
                    'The gene ' + gi.id + ' is repeated twice in the ' +
                    config.gene_info_file + ' file')

            genes[gi.id] = gi
            _addNSTokenToGeneInfo(nsTokens, "id", gi.id, gi)
            _addNSTokenToGeneInfo(nsTokens, "sym", gi.sym, gi)
            for s in gi.syns:
                _addNSTokenToGeneInfo(nsTokens, "syns", s, gi)
    print("loaded ", len(genes), "genes", file=sys.stderr)

    return genes, nsTokens


def _addNSTokenToGeneInfo(nsTokens, ns, token, gi):
    if ns not in nsTokens:
        nsTokens[ns] = {}
    tokens = nsTokens[ns]
    if token not in tokens:
        tokens[token] = []
    tokens[token].append(gi)


def getCleanGeneId(config, ns, t):
    ns_tokens = getNsTokens(config)

    if ns not in ns_tokens:
        return
    allTokens = ns_tokens[ns]
    if t not in allTokens:
        return
    if len(allTokens[t]) != 1:
        return
    return allTokens[t][0].id


def getGenes(config):
    if config.genes is None:
        genes, ns_tokens = _parseNCBIGeneInfo(config)
        config.genes = genes
        config.nsTokes = ns_tokens
    return config.genes


def getNsTokens(config):
    if config.ns_tokens is None:
        genes, ns_tokens = _parseNCBIGeneInfo(config)
        config.genes = genes
        config.nsTokes = ns_tokens
    return config.ns_tokens
