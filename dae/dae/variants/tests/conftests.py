import os


def relative_to_this_test_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)
