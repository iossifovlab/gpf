import copy
from typing import Dict, Any
from collections import OrderedDict
from box import Box


class Schema(object):

    # New types only need to be added here.
    type_map: Dict[str, Any] = OrderedDict([
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

    def create_column(self, col_name, col_type):
        if col_name not in self.columns:
            self.columns[col_name] = Schema.produce_type(col_type)

    def remove_column(self, col_name):
        if col_name in self.columns:
            del(self.columns[col_name])

    def order_as(self, ordered_col_names):
        ordered_schema = Schema()
        for col in ordered_col_names:
            assert col in self.columns, [col, self.col_names]
            ordered_schema.columns[col] = self.columns[col]
        return ordered_schema

    @classmethod
    def from_dict(cls, schema_dict):
        new_schema = Schema()
        assert isinstance(schema_dict, dict)
        for col_type in cls.type_map.keys():
            if col_type not in schema_dict:
                # TODO Should this skip the faulty col_type
                # or exit with an error? (or just print out an error?)
                continue
            for col in schema_dict[col_type]:
                new_schema.create_column(col, col_type)
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

    @staticmethod
    def diff_schemas(left, right):
        result = copy.deepcopy(left)
        for key in right.columns:
            if key in result.columns:
                del result.columns[key]
        return result

    @property
    def col_names(self):
        return list(self.columns.keys())

    def __str__(self):
        ret_str = ""
        for col, col_type in self.columns.items():
            ret_str += '{} -> [{}]\n'.format(col, col_type.type_py)
        return ret_str

    def __contains__(self, key):
        return key in self.columns

    def __delitem__(self, key):
        del self.columns[key]

    def __getitem__(self, key):
        return self.columns.__getitem__(key)
