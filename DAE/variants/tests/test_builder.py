'''
Created on Mar 19, 2018

@author: lubo
'''
import shutil
from variants.configure import Configure
from variants.tests.conftest import relative_to_this_test_folder
import os
from variants.builder import variants_builder as VB


def test_variants_build_multi(temp_dirname):

    conf = Configure.from_prefix(
        relative_to_this_test_folder("fixtures/trios_multi"))

    shutil.copy(conf.pedigree, temp_dirname)
    shutil.copy(conf.vcf, temp_dirname)

    prefix = os.path.join(temp_dirname, "trios_multi")

    fvars = VB(prefix)
    assert fvars is not None
    conf = Configure.from_prefix(prefix)

    assert os.path.exists(conf.annotation)
