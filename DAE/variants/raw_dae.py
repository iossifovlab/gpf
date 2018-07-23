'''
Created on Jul 23, 2018

@author: lubo
'''
import os

from variants.configure import Configure
from variants.family import FamiliesBase


class RawDaeVariants(FamiliesBase):

    def __init__(self, config=None, prefix=None, region=None):
        super(RawDaeVariants, self).__init__()

        if prefix is not None:
            config = Configure.from_prefix_dae(prefix)

        assert isinstance(config, Configure)
        self.config = config.dae

        assert os.path.exists(config.dae.summary_filename)
        assert os.path.exists(config.dae.toomany_filename)
        assert os.path.exists(config.dae.family_filename)
