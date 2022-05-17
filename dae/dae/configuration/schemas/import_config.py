from dae.backends.dae.loader import DenovoLoader, DaeTransmittedLoader
from dae.backends.vcf.loader import VcfLoader
from dae.backends.cnv.loader import CNVLoader
from dae.pedigrees.loader import FamiliesLoader


def _to_list(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, str):
        return list(
            map(str.strip, obj.split(","))
        )
    return obj


def _int_shorthand(obj):
    try:
        unit_suffixes = {
            "K": 1_000,
            "M": 1_000_000,
            "G": 1_000_000_000,
        }
        return int(obj[:-1]) * unit_suffixes[obj[-1].upper()]
    except Exception:
        return obj


_region_chromosomes_schema = {
    "region_length": {"type": "integer", "coerce": _int_shorthand},
    "chromosomes": {
        "type": "list",
        "schema": {"type": "string"},
        "coerce": _to_list,
    },
}

_loader_processing_params = {
    "row_group_size": {"type": "integer", "coerce": _int_shorthand},
    **_region_chromosomes_schema,
}

_loader_processing_schema = {
    "anyof": [
        {
            "type": "dict",
            "schema": _loader_processing_params
        },
        {
            "type": "string",
            "allowed": ["single_bucket", "chromosome"],
        },
    ],
}

import_config_schema = {
    "id": {"type": "string"},
    "input": {
        "type": "dict",
        "schema": {
            "vcf": {
                "type": "dict",
                "schema": {},
            },
            "denovo": {
                "type": "dict",
                "schema": {},
            },
            "cnv": {
                "type": "dict",
                "schema": {},
            },
            "dae": {
                "type": "dict",
                "schema": {},
            },
            "pedigree": {
                "type": "dict",
                "schema": {
                    "file": {"type": "string", "required": True},
                },
            },
            "input_dir": {"type": "string"}
        },
    },
    "processing_config": {
        "type": "dict",
        "schema": {
            "work_dir": {"type": "string"},
            "vcf": _loader_processing_schema,
            "denovo": _loader_processing_schema,
            "cnv": _loader_processing_schema,
            "dae": _loader_processing_schema,
        },
    },
    "destination": {
        "type": "dict",
        "schema": {
            "storage_id": {"type": "string"},
        },
    },
    "partition_description": {
        "type": "dict",
        "schema": {
            "region_bin": {
                "type": "dict",
                "schema": _region_chromosomes_schema,
            },
            "family_bin": {
                "type": "dict",
                "schema": {
                    "family_bin_size": {"type": "integer"},
                }
            },
            "frequency_bin": {
                "type": "dict",
                "schema": {
                    "rare_boundary": {"type": "integer"},
                }
            },
            "coding_bin": {
                "type": "dict",
                "schema": {
                    "coding_effect_types": {"type": "string"},
                }
            },
        }
    },
}


def _fill_with_loader_arguments():
    _set_loader_args(
        VcfLoader,
        import_config_schema["input"]["schema"]["vcf"]["schema"],
        "vcf_")
    _set_loader_args(
        DenovoLoader,
        import_config_schema["input"]["schema"]["denovo"]["schema"],
        "denovo_")
    _set_loader_args(
        CNVLoader,
        import_config_schema["input"]["schema"]["cnv"]["schema"],
        "cnv_")
    _set_loader_args(
        DaeTransmittedLoader,
        import_config_schema["input"]["schema"]["dae"]["schema"],
        "dae_")
    _copy_loader_args(
        FamiliesLoader,
        import_config_schema["input"]["schema"]["pedigree"]["schema"],
        "ped_")


def _set_loader_args(loader_cls, schema, prefix):
    schema["files"] = {
        "type": "list",
        "required": True,
        "valuesrules": {"type": "string"},
    }
    _copy_loader_args(loader_cls, schema, prefix)


def _copy_loader_args(loader_cls, schema, prefix):
    for arg in loader_cls._arguments():
        if not arg.argument_name.startswith("--"):
            # ignore positional arguments as they are explicitly
            # specified in the schema
            continue
        arg_config = {}
        arg_name = arg.argument_name.strip("-")\
            .replace('-', '_').removeprefix(prefix)
        if arg.value_type is not None:
            arg_config["type"] = {
                str: "string",
                bool: "boolean",
                int: "integer",
                float: "float",
            }[arg.value_type]
        if arg.default_value is not None:
            arg_config["default"] = arg.default_value
        schema[arg_name] = arg_config


_fill_with_loader_arguments()
