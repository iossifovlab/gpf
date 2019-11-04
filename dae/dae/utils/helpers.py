import os
from dae.pedigrees.pedigree_reader import PedigreeReader


def pedigree_from_path(filepath):
    ped_df = PedigreeReader.load_pedigree_file(filepath)
    study_id = os.path.splitext(os.path.basename(filepath))[0]
    return ped_df, study_id
