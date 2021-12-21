from __future__ import annotations

import logging

from typing import Dict, Optional

logger = logging.getLogger(__name__)


class Schema:

    class Source:
        def __init__(
                self, annotator_type: str,
                annotator_config: dict, attribute_config: dict):
            self.annotator_type = annotator_type
            self.annotator_config = annotator_config
            self.attribute_config = attribute_config

        def __repr__(self):
            return f"source: {self.annotator_type}> " \
                f"{self.annotator_config}:{self.attribute_config}"

    class Field:

        def __init__(
                self, name: str,
                py_type: str,
                internal: bool = False,
                description: Optional[str] = None,
                source: Optional[Schema.Source] = None):

            self.name: str = name
            self.type: str = py_type
            self.internal: bool = internal
            self.description: str = description

            self.source: Optional[Schema.Source] = source

    def __init__(self):
        self.fields: Dict[str, Schema.Field] = {}

    def create_field(
            self, name: str, py_type: str,
            internal: bool = False,
            description: Optional[str] = None,
            source: Optional[Source] = None):
        if name in self.fields:
            logger.warning(
                f"creating a field with name {name} more than once")

        self.fields[name] = Schema.Field(
            name, py_type, internal, description, source)

    @staticmethod
    def merge_schemas(left: Schema, right: Schema) -> Schema:
        merged_schema = Schema()
        missing_fields = {}
        for field_name, field in right.fields.items():
            if field_name in left.fields:
                left.fields[field_name] = field
            else:
                missing_fields[field_name] = field
        merged_schema.fields.update(left.fields)
        merged_schema.fields.update(missing_fields)
        return merged_schema

    @staticmethod
    def concat_schemas(first: Schema, second: Schema) -> Schema:
        result = Schema()
        result.fields.update(first.fields)

        for name, field in second.fields.items():
            if name in result:
                message = f"two schemas has fields with the same name: " \
                    f"first {first[name]}; second {field}"
                logger.error(message)
                raise ValueError(message)
            result.fields[name] = field

        return result

    @property
    def names(self):
        return list(self.fields.keys())

    @property
    def public_fields(self):
        return [
            key for key, field in self.fields.items() if not field.internal
        ]

    @property
    def internal_fields(self):
        return [
            key for key, field in self.fields.items() if field.internal
        ]

    def __repr__(self):
        ret_str = ""
        for field_name, field in self.fields.items():
            if not field.internal:
                ret_str += f"\t{field_name} -> [{field.type}]\n"
            else:
                ret_str += f"\t{field_name} -> [{field.type}, <internal>] \n"

        return ret_str

    def __contains__(self, key):
        return key in self.names

    def __delitem__(self, key):
        del self.fields[key]

    def __getitem__(self, key):
        return self.fields.__getitem__(key)

    def __len__(self):
        return len(self.names)
