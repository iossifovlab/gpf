'''
Created on Feb 16, 2017

@author: lubo
'''
from Config import Config
import ConfigParser
from GeneInfoDB import GeneInfoDB


class GeneInfoConfig(object):
    """
    Helper class for accessing DAE and geneInfo configuration.
    """

    def __init__(self, *args, **kwargs):
        super(GeneInfoConfig, self).__init__(*args, **kwargs)
        self.dae_config = Config()

        wd = self.dae_config.daeDir
        self.config = ConfigParser.SafeConfigParser({'wd': wd})
        self.config.read(self.dae_config.geneInfoDBconfFile)
        print(self.dae_config.geneInfoDBconfFile, self.dae_config.daeDir)
        self.gene_info = GeneInfoDB(
            self.dae_config.geneInfoDBconfFile, self.dae_config.daeDir)

    @staticmethod
    def list_gene_weights():
        """
        Lists all available gene weights configured in `geneInfo.conf`.
        """
        dae_config = Config()
        wd = dae_config.daeDir
        config = ConfigParser.SafeConfigParser({'wd': wd})
        config.read(dae_config.geneInfoDBconfFile)

        weights = config.get('geneWeights', 'weights')
        names = [n.strip() for n in weights.split(',')]
        return names
