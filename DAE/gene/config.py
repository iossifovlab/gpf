'''
Created on Feb 16, 2017

@author: lubo
'''
from builtins import object
from Config import Config
from future import standard_library
standard_library.install_aliases()
from configparser import ConfigParser
from GeneInfoDB import GeneInfoDB


class GeneInfoConfig(object):
    """
    Helper class for accessing DAE and geneInfo configuration.
    """

    def __init__(self, *args, **kwargs):
        super(GeneInfoConfig, self).__init__(*args, **kwargs)
        self.dae_config = Config()

        wd = self.dae_config.daeDir
        data_dir = self.dae_config.data_dir

        self.config = ConfigParser({
            'wd': wd,
            'data': data_dir
        })
        self.config.read(self.dae_config.geneInfoDBconfFile)
        self.gene_info = GeneInfoDB(
            self.dae_config.geneInfoDBconfFile,
            self.dae_config.daeDir,
            self.dae_config.data_dir)

    @staticmethod
    def list_gene_weights():
        """
        Lists all available gene weights configured in `geneInfo.conf`.
        """
        dae_config = Config()
        wd = dae_config.daeDir
        data_dir = dae_config.data_dir

        config = ConfigParser({
            'wd': wd,
            'data': data_dir,
        })
        config.read(dae_config.geneInfoDBconfFile)

        weights = config.get('geneWeights', 'weights')
        names = [n.strip() for n in weights.split(',')]
        return names
