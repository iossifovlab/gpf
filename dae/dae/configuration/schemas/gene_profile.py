from dae.configuration.utils import validate_existing_path
from dae.variants.attributes import (
    _ROLE_DISPLAY_NAME,
    _VARIANT_TYPE_DISPLAY_NAME,
)

variant_types = list(_VARIANT_TYPE_DISPLAY_NAME.keys()) + \
    list(_VARIANT_TYPE_DISPLAY_NAME.values())

roles = list(_ROLE_DISPLAY_NAME.keys()) + \
    list(_ROLE_DISPLAY_NAME.values())


gene_set_schema = {
    "type": "dict",
    "schema": {
        "collection_id": {
            "type": "string",
            "regex": "^[^.\r\n]+$",
            "default": "main",
        },
        "display_name": {"type": "string"},
        "meta": {"type": "string"},
        "default_visible": {"type": "boolean", "default": True},
        "set_id": {"type": "string", "regex": "^[^.\r\n]+$"},
    },
}

gene_score_schema = {
    "type": "dict",
    "schema": {
        "score_name": {"type": "string", "regex": "^[^.\r\n]+$"},
        "display_name": {"type": "string"},
        "meta": {"type": "string"},
        "default_visible": {"type": "boolean", "default": True},
        "format": {"type": "string", "default": "%s"},
    },
}

gene_profile_link_schema = {
    "name": {"type": "string"},
    "url": {"type": "string"},
}

variant_statistic_schema = {
    "type": "dict",
    "schema": {
        "id": {"type": "string", "regex": "^[^.\r\n]+$", "required": True},
        "display_name": {"type": "string", "required": True},
        "description": {"type": "string"},
        "effects": {"type": "list", "schema": {"type": "string"}},
        "category": {"type": "string", "allowed": ["denovo", "rare"]},
        "genomic_scores": {"type": "list", "schema": {
            "type": "dict",
            "schema": {
                "name": {"type": "string", "regex": "^[^.\r\n]+$"},
                "min": {"type": "float", "default": None, "nullable": True},
                "max": {"type": "float", "default": None, "nullable": True},
                "values": {
                  "type": "list",
                  "default": None,
                  "nullable": True,
                  "schema": {"type": "string"},
                },
            },
        }},
        "default_visible": {"type": "boolean", "default": True},
        "variant_types": {
            "type": "list",
            "schema": {
                "type": "string",
                "allowed": variant_types,
            },
        },
        "roles": {
            "type": "list",
            "schema": {
                "type": "string",
                "allowed": roles,
            },
        },
    },
}

gene_profiles_config = {
    "conf_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "required": True,
    },

    "gene_sets": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": {
                "category": {"type": "string", "regex": "^[^.\r\n]+$"},
                "display_name": {"type": "string"},
                "default_visible": {"type": "boolean", "default": True},
                "sets": {"type": "list", "schema": gene_set_schema},
            },
        },
    },
    "description": {"type": "string"},
    "gene_scores": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": {
                "category": {"type": "string", "regex": "^[^.\r\n]+$"},
                "display_name": {"type": "string"},
                "default_visible": {"type": "boolean", "default": True},
                "scores": {"type": "list", "schema": gene_score_schema},
            },
        },
    },
    "datasets": {
        "required": True,
        "type": "dict",
        "valuesrules": {
            "type": "dict", "schema": {
                "meta": {"type": "string"},
                "person_sets": {"type": "list", "schema": {
                    "type": "dict",
                    "schema": {
                        "set_name": {
                            "type": "string",
                            "regex": "^[^.\r\n]+$",
                        },
                        "collection_name": {"type": "string"},
                        "description": {"type": "string"},
                        "default_visible": {
                            "type": "boolean", "default": True},
                    },
                }},
                "statistics": {
                    "type": "list", "schema": variant_statistic_schema,
                },
                "default_visible": {"type": "boolean", "default": True},
                "display_name": {"type": "string"},
            },
        },
    },
    "default_dataset": {"type": "string", "required": True},
    "order": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "string",
        },
    },
    "gene_links": {
        "type": "list",
        "default": [],
        "valuesrules": {
            "type": "dict",
            "schema": gene_profile_link_schema,
            "allow_unknown": True,
        },
    },
}
