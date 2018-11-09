from collections import OrderedDict
from box import Box


class Schema(object):

    # New types only need to be added here.
    type_map = OrderedDict([
                ('str', str),
                ('float', float),
                ('int', int),
                ('list(str)', str),
                ('list(float)', float),
                ('list(int)', int)])

    def __init__(self):
        self.columns = OrderedDict()

    @classmethod
    def produce_type(cls, type_name):
        assert type_name in cls.type_map
        return Box({'type_name': type_name,
                    'type_py': cls.type_map[type_name]},
                   default_box=True,
                   default_box_attr=None)

    @classmethod
    def from_dict(cls, schema_dict):
        new_schema = Schema()
        assert type(schema_dict) is dict
        for col_type in cls.type_map.keys():
            if col_type not in schema_dict:
                continue
            col_list = schema_dict[col_type]
            col_list.replace(' ', '')
            col_list.replace('\t', '')
            col_list.replace('\n', '')
            for col in col_list.split(','):
                new_schema.columns[col] = cls.produce_type(col_type)
        return new_schema

    @staticmethod
    def merge_schemas(left, right):
        merged_schema = Schema()
        missing_columns = OrderedDict()
        for col_name, col_type in right.columns.items():
            if col_name in left.columns:
                left.columns[col_name] = col_type
            else:
                missing_columns[col_name] = col_type
        merged_schema.columns.update(left.columns)
        merged_schema.columns.update(missing_columns)
        return merged_schema

    def __str__(self):
        ret_str = ""
        for col, col_type in self.columns.items():
            ret_str += '{} -> [{}]\n'.format(col, col_type.type_py)
        return ret_str
