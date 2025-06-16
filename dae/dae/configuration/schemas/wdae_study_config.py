from dae.configuration.schemas.person_sets import person_set_collections_schema
from dae.configuration.schemas.study_config import (
    denovo_gene_sets_schema,
    enrichment_schema,
    genotype_browser_schema,
    genotype_storage_schema,
)

wdae_gene_browser_schema = {
    "type": "dict",
    "schema": {
        "enabled": {"type": "boolean", "required": True},
        "frequency_column": {"type": "string"},
        "frequency_name": {"type": "string"},
        "effect_column": {"type": "string"},
        "location_column": {"type": "string"},
        "domain_min": {
            "type": "float",
            "forbidden": [0.0],
            "min": 0.0,
            "max": 100.0,
        },
        "domain_max": {
            "type": "float",
            "forbidden": [0.0],
            "min": 0.0,
            "max": 100.0,
        },
        "has_affected_status": {"type": "boolean", "default": True},
    },
}

wdae_common_report_schema = {
    "type": "dict",
    "schema": {
        "enabled": {"type": "boolean", "required": True},
        "selected_person_set_collections": {
            "type": "dict",
            "schema": {
                "denovo_report": {
                    "type": "list", "schema": {"type": "string"},
                },
                "family_report": {
                    "type": "list", "schema": {"type": "string"},
                },
            },
            "default": {},
        },
        "effect_groups": {
            "type": "list",
            "schema": {"type": "string"},
            "default": ["LGDs", "nonsynonymous", "UTRs"],
        },
        "effect_types": {
            "type": "list",
            "schema": {"type": "string"},
            "default": [
                "Nonsense", "Frame-shift", "Splice-site", "Missense",
                "No-frame-shift", "noStart", "noEnd", "Synonymous",
                "Non coding", "Intron", "Intergenic", "3'-UTR", "5'-UTR",
            ],
        },
        "draw_all_families": {"type": "boolean", "default": False},
        "file_path": {
            "type": "string",
        },
    },
    "default": {"enabled": False},
}

wdae_study_config_schema = {
    "id": {"type": "string", "required": True},
    "name": {"type": "string"},
    "enabled": {"type": "boolean"},
    "work_dir": {
        "type": "string",
    },
    "conf_dir": {
        "type": "string",
    },
    "phenotype_data": {"type": "string", "default": ""},
    "phenotype_browser": {"type": "boolean"},
    "phenotype_tool": {"type": "boolean"},
    "description_file": {
        "type": "string",
        "coerce": "abspath",
        "default": "description.md",
    },
    "description_editable": {"type": "boolean", "default": True},
    "study_type": {"type": "list", "schema": {"type": "string"}},
    "year": {"type": "list", "schema": {"type": "integer"}},
    "pub_med": {"type": "list", "schema": {"type": "string"}},
    "genome": {
        "type": "string",
        "nullable": True,
        "meta": {"deprecated": True},
    },
    "study_phenotype": {"type": "string"},
    "chr_prefix": {
        "type": "boolean",
        "nullable": True,
        "meta": {"deprecated": True},
    },
    "has_present_in_child": {"type": "boolean"},
    "has_present_in_parent": {"type": "boolean"},
    "has_denovo": {"type": "boolean", "default": True},
    "has_zygosity": {"type": "boolean", "default": False},
    "has_transmitted": {"type": "boolean"},
    "has_complex": {"type": "boolean"},
    "has_cnv": {"type": "boolean"},
    "has_tandem_repeat": {"type": "boolean"},
    "has_genotype": {"type": "boolean", "default": True},
    "genotype_storage": {
        "type": "dict",
        "schema": genotype_storage_schema,
        "excludes": "studies",
    },
    "studies": {
        "type": "list",
        "schema": {"type": "string"},
        "excludes": "genotype_storage",
    },
    "genotype_browser": genotype_browser_schema,
    "common_report": wdae_common_report_schema,
    "denovo_gene_sets": denovo_gene_sets_schema,
    "enrichment": enrichment_schema,
    "gene_browser": wdae_gene_browser_schema,
    "person_set_collections": person_set_collections_schema,
}
