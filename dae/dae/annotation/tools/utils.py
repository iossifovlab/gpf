from importlib import import_module


class AnnotatorInitializer(object):

    @staticmethod
    def _split_class_name(class_fullname):
        splitted = class_fullname.split('.')
        module_path = splitted[:-1]
        assert len(module_path) >= 1
        if len(module_path) == 1:
            res = ["dae", "annotation", "tools"]
            res.extend(module_path)
            module_path = res

        module_name = '.'.join(module_path)
        class_name = splitted[-1]

        return module_name, class_name

    @classmethod
    def _name_to_class(cls, class_fullname):
        module_name, class_name = cls._split_class_name(class_fullname)
        module = import_module(module_name)
        clazz = getattr(module, class_name)
        return clazz

    @classmethod
    def instantiate(cls, annotator_config):
        clazz = cls._name_to_class(annotator_config.annotator_name)
        assert clazz is not None
        return clazz(annotator_config)


def handle_header(source_header):
    header = []
    for index, col_name in enumerate(source_header):
        col = col_name.strip('#')
        if col in header:
            col = "{}_{}".format(col, index)
        header.append(col)
    return header


class LineMapper(object):

    def __init__(self, source_header):
        self.source_header = handle_header(source_header)

    def map(self, source_line):
        return dict(zip(self.source_header, source_line))
