import gzip
import os
from importlib import import_module


class AnnotatorFactory:
    @staticmethod
    def _split_class_name(class_fullname):
        splitted = class_fullname.split(".")
        module_path = splitted[:-1]
        assert len(module_path) >= 1
        if len(module_path) == 1:
            res = ["dae", "annotation", "tools"]
            res.extend(module_path)
            module_path = res

        module_name = ".".join(module_path)
        class_name = splitted[-1]

        return module_name, class_name

    @classmethod
    def name_to_class(cls, class_fullname):
        module_name, class_name = cls._split_class_name(class_fullname)
        module = import_module(module_name)
        clazz = getattr(module, class_name)
        return clazz

    @classmethod
    def make_annotator(cls, annotator_config, genomes_db, liftover=None):
        clazz = cls.name_to_class(annotator_config.annotator)
        assert clazz is not None
        return clazz(annotator_config, genomes_db, liftover)


def handle_chrom_prefix(expect_prefix, data):
    if data is None:
        return data
    if expect_prefix and not data.startswith("chr"):
        return "chr{}".format(data)
    if not expect_prefix and data.startswith("chr"):
        return data[3:]
    return data


def is_gzip(filename):
    try:
        if filename == "-" or not os.path.exists(filename):
            return False
        with gzip.open(filename, "rt") as infile:
            infile.readline()
        return True
    except Exception:
        return False


def is_tabix(filename):
    return is_gzip(filename) and os.path.exists("{}.tbi".format(filename))


def regions_intersect(b1: int, e1: int, b2: int, e2: int) -> bool:
    return (
        b2 <= b1 <= e2
        or b2 <= e1 <= e2
        or b1 <= b2 <= e1
        or b1 <= e2 <= e1
    )
