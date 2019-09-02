'''
Created on Feb 16, 2017

@author: lubo
'''
import sys
from box import Box

from dae.configuration.dae_config_parser import ConfigParserBase

from dae.gene.gene_weight_config_parser import GeneWeightConfigParser
from dae.gene.gene_term import loadGeneTerm


class GeneInfoConfigParser(ConfigParserBase):
    """
    Helper class for accessing DAE and geneInfo configuration.
    """

    @classmethod
    def parse(cls, config):
        config[GeneInfoDB.SECTION] = \
            GeneInfoDB.parse(config.get(GeneInfoDB.SECTION, None))
        config['geneWeights'] = GeneWeightConfigParser.parse(config)

        return config

    @staticmethod
    def getGeneTermAtt(config, gt_id, attName):
        if gt_id in config.gene_terms and \
                config.gene_terms[gt_id].get(attName, None):
            return config.gene_terms[gt_id][attName]

    @classmethod
    def getGeneTerms(cls, config, gt_id='main', inNS='sym'):
        fl = config.gene_terms[gt_id].file
        gt = loadGeneTerm(fl)
        if not inNS:
            return gt
        if gt.geneNS == inNS:
            return gt
        if gt.geneNS == 'id' and inNS == 'sym':
            def rF(x):
                if x in config.gene_info.genes:
                    return config.gene_info.genes[x].sym
            gt.renameGenes('sym', rF)
        elif gt.geneNS == 'sym' and inNS == 'id':
            gt.renameGenes(
                'id',
                lambda x: GeneInfoDB.getCleanGeneId(config.gene_info, 'sym', x)
            )
        else:
            raise Exception(
                'Unknown name space for the ' + gt_id + ' gene terms: |'
                + gt.geneNS + '|' + inNS + '|')
        return gt


class GeneInfoDB(ConfigParserBase):

    SECTION = 'geneInfo'

    @classmethod
    def parse(cls, config):
        if config is None:
            return

        genes, ns_tokens = cls._parseNCBIGeneInfo(config)

        config['genes'] = genes
        config['nsTokens'] = ns_tokens

        return config

    @classmethod
    def _parseNCBIGeneInfo(cls, config):
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
                cls._addNSTokenToGeneInfo(nsTokens, "id", gi.id, gi)
                cls._addNSTokenToGeneInfo(nsTokens, "sym", gi.sym, gi)
                for s in gi.syns:
                    cls._addNSTokenToGeneInfo(nsTokens, "syns", s, gi)
        print("loaded ", len(genes), "genes", file=sys.stderr)

        return genes, nsTokens

    @staticmethod
    def _addNSTokenToGeneInfo(nsTokens, ns, token, gi):
        if ns not in nsTokens:
            nsTokens[ns] = {}
        tokens = nsTokens[ns]
        if token not in tokens:
            tokens[token] = []
        tokens[token].append(gi)

    @staticmethod
    def getCleanGeneId(config, ns, t):
        if ns not in config.nsTokens:
            return
        allTokens = config.nsTokens[ns]
        if t not in allTokens:
            return
        if len(allTokens[t]) != 1:
            return
        return allTokens[t][0].id
