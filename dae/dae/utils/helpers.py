import os


def study_id_from_path(filepath):
    return os.path.splitext(os.path.basename(filepath))[0]


def str2bool(value):
    return value.lower in {'true', 'yes', '1', 't', 'y'}
