'''
Created on Feb 16, 2017

@author: lubo
'''
import sys
from box import Box

from configurable_entities.configuration import DAEConfig
from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig

from gene.gene_weight_config import GeneWeightConfig
from gene.gene_term_config import GeneTermConfig
from gene.chromosome_config import ChromosomeConfig
from gene.gene_term import loadGeneTerm


class GeneInfoConfig(ConfigurableEntityConfig):
    """
    Helper class for accessing DAE and geneInfo configuration.
    """

    def __init__(self, config=None, *args, **kwargs):
        super(GeneInfoConfig, self).__init__(config, *args, **kwargs)

    @classmethod
    def from_config(cls, dae_config=None):
        if dae_config is None:
            dae_config = DAEConfig()

        config = cls.read_config(
            dae_config.gene_info_conf, dae_config.dae_data_dir)

        config = Box(config)

        parsed_config = {}

        parsed_config['geneInfo'] = GeneInfoDB.from_config(
            config.get('GeneInfo', None))
        parsed_config['geneWeights'] = GeneWeightConfig.from_config(config)
        parsed_config['geneTerms'] = GeneTermConfig.from_config(config)
        parsed_config['chromosomes'] = ChromosomeConfig.from_config(
            config.get('chromosomes', None))

        return GeneInfoConfig(parsed_config)

    def getGeneTermIds(self):
        return self.gene_terms.keys()

    def getGeneTermAtt(self, gt_id, attName):
        if gt_id in self.gene_terms and \
                self.gene_terms[gt_id].get(attName, None):
            return self.gene_terms[gt_id][attName]

    def getGeneTerms(self, gt_id='main', inNS='sym'):
        fl = self.gene_terms[gt_id].file
        gt = loadGeneTerm(fl)
        if not inNS:
            return gt
        if gt.geneNS == inNS:
            return gt
        if gt.geneNS == 'id' and inNS == 'sym':
            def rF(x):
                if x in self.gene_info.genes:
                    return self.gene_info.genes[x].sym
            gt.renameGenes('sym', rF)
        elif gt.geneNS == 'sym' and inNS == 'id':
            gt.renameGenes(
                'id', lambda x: self.gene_info.getCleanGeneId('sym', x))
        else:
            raise Exception(
                'Unknown name space for the ' + gt_id + ' gene terms: |'
                + gt.geneNS + '|' + inNS + '|')
        return gt


class GeneInfoDB(ConfigurableEntityConfig):

    def __init__(self, config=None, *args, **kwargs):
        super(GeneInfoDB, self).__init__(config, *args, **kwargs)

        self._genes = None
        self._nsTokens = None

    @classmethod
    def from_config(cls, config):
        if config is None:
            return

        return GeneInfoDB(config)

    @property
    def genes(self):
        if self._genes is None:
            self._parseNCBIGeneInfo()
        return self._genes

    @property
    def nsTokens(self):
        if self._nsTokens is None:
            self._parseNCBIGeneInfo()
        return self._nsTokens

    def _parseNCBIGeneInfo(self):
        self._genes = {}
        self._nsTokens = {}
        with open(self.gene_info_file) as f:
            for line in f:
                if line[0] == "#":
                    # print "COMMENT: ", line
                    continue
                cs = line.strip().split("\t")
                if len(cs) != 15:
                    raise Exception(
                        'Unexpected line in the ' + self.gene_info_file)

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

                if (gi.id in self._genes):
                    raise Exception(
                        'The gene ' + gi.id + ' is repeated twice in the ' +
                        self.gene_info_file + ' file')

                self._genes[gi.id] = gi
                self._addNSTokenToGeneInfo("id", gi.id, gi)
                self._addNSTokenToGeneInfo("sym", gi.sym, gi)
                for s in gi.syns:
                    self._addNSTokenToGeneInfo("syns", s, gi)
        print("loaded ", len(self._genes), "genes", file=sys.stderr)

    def _addNSTokenToGeneInfo(self, ns, token, gi):
        if ns not in self._nsTokens:
            self._nsTokens[ns] = {}
        tokens = self._nsTokens[ns]
        if token not in tokens:
            tokens[token] = []
        tokens[token].append(gi)

    def getCleanGeneId(self, ns, t):
        if ns not in self.nsTokens:
            return
        allTokens = self.nsTokens[ns]
        if t not in allTokens:
            return
        if len(allTokens[t]) != 1:
            return
        return allTokens[t][0].id
