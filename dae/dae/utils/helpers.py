import os
from dae.pedigrees.pedigree_reader import PedigreeReader


def pedigree_from_path(filepath, family_format='pedigree'):
    if family_format == 'pedigree':
        ped_df = PedigreeReader.flexible_pedigree_read(filepath)
    elif family_format == 'simple':
        ped_df = PedigreeReader.load_simple_family_file(filepath)
    else:
        raise NotImplementedError(
            'unsupported file format:' + family_format)

    study_id = os.path.splitext(os.path.basename(filepath))[0]
    return ped_df, study_id