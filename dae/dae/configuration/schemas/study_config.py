from dae.configuration.schemas.person_sets import person_set_collections_schema
from dae.configuration.utils import validate_existing_path, validate_path

phenotype_schema = {
    "type": "dict",
    "schema": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "color": {"type": "string"},
    },
}

genotype_column_schema = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
        "source": {"type": "string"},
        "format": {"type": "string", "default": "%s"},
    },
}

phenotype_column_schema = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
        "source": {"type": "string"},
        "format": {"type": "string", "default": "%s"},
        "role": {"type": "string"},
    },
}

column_group_schema = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
        "columns": {"type": "list", "schema": {"type": "string"}},
    },
}

counting_schema = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "desc": {"type": "string"},
}

counting_defaults = {
    "enrichment_events_counting": {
        "id": "enrichment_events_counting",
        "name": "Counting events",
        "desc": "Counting events",
    },
    "enrichment_gene_counting": {
        "id": "enrichment_gene_counting",
        "name": "Counting affected genes",
        "desc": "Counting affected genes",
    },
}

person_filters_schema = {
    "name": {"type": "string"},
    "from": {"type": "string", "allowed": ["pedigree", "phenodb"]},
    "source": {"type": "string"},
    "source_type": {
        "type": "string",
        "allowed": ["continuous", "categorical"],
    },
    "filter_type": {"type": "string"},
}

family_filters_schema = dict(  # pylint: disable=use-dict-literal
    **person_filters_schema,
    role={"type": "string"},
)

genotype_browser_schema = {
    "type": "dict",
    "schema": {
        "enabled": {"type": "boolean", "required": True},
        "has_family_filters": {"type": "boolean"},
        "has_family_pheno_filters": {
          "type": "boolean",
          "required": False,
        },
        "has_family_structure_filter": {
            "type": "boolean",
            "dependencies": {
                "has_family_filters": [True],
            },
        },
        "has_person_filters": {"type": "boolean"},
        "has_person_pheno_filters": {
          "type": "boolean",
          "required": False,
        },
        "has_study_filters": {
            "type": "boolean",
            "depends_global": "studies",
        },
        "has_present_in_child": {"type": "boolean"},
        "has_present_in_parent": {"type": "boolean"},
        "has_pedigree_selector": {"type": "boolean"},
        "has_study_types": {"type": "boolean"},
        "has_graphical_preview": {"type": "boolean"},
        "show_all_unknown": {"type": "boolean", "default": False},

        "inheritance_type_filter": {
            "type": "list",
            "schema": {"type": "string"},
        },
        "selected_inheritance_type_filter_values": {
            "type": "list",
            "schema": {"type": "string"},
            "dependencies": ["inheritance_type_filter"],
        },
        "columns": {
            "type": "dict",
            "schema": {
                "genotype": {
                    "type": "dict",
                    "valuesrules": genotype_column_schema,
                },
                "phenotype": {
                    "type": "dict",
                    "valuesrules": phenotype_column_schema,
                },
            },
        },
        "column_groups": {
            "type": "dict",
            "valuesrules": column_group_schema,
        },
        "preview_columns": {
            "type": "list", "schema": {"type": "string"},
        },
        "preview_columns_ext": {
            "type": "list", "schema": {"type": "string"},
        },
        "download_columns": {
            "type": "list", "schema": {"type": "string"},
        },
        "download_columns_ext": {
            "type": "list", "schema": {"type": "string"},
        },
        "summary_preview_columns": {
            "type": "list", "schema": {"type": "string"},
        },
        "summary_download_columns": {
            "type": "list", "schema": {"type": "string"},
        },
        "person_filters": {
            "type": "dict",
            "valuesrules": {
                "type": "dict",
                "schema": person_filters_schema,
            },
        },
        "family_filters": {
            "type": "dict",
            "valuesrules": {
                "type": "dict",
                "schema": family_filters_schema,
            },
        },
        "variant_types": {
            "type": "list",
            "schema": {"type": "string"},
            "default": ["sub", "ins", "del"],
        },
        "selected_variant_types": {
            "type": "list",
            "schema": {"type": "string"},
            "default": ["sub", "ins", "del"],
        },
        "max_variants_count": {
            "type": "integer",
            "default": 1000,
        },
    },
}

family_schema = {
    "path": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "required": True,
    },
    "params": {
        "type": "dict",
        "schema": {
            "ped_file": {"type": "string"},
            "ped_family": {"type": "string"},
            "ped_person": {"type": "string"},
            "ped_mom": {"type": "string"},
            "ped_dad": {"type": "string"},
            "ped_sex": {"type": "string"},
            "ped_status": {"type": "string"},
            "ped_role": {"type": "string"},
            "ped_no_role": {"type": "boolean"},
            "ped_proband": {"type": "string"},
            "ped_no_header": {"type": "boolean"},
            "ped_file_format": {"type": "string"},
            "ped_layout_mode": {"type": "string"},
            "ped_sep": {"type": "string"},
            "ped_tags": {"type": "boolean"},
            "ped_no_tags": {"type": "boolean"},
        },
        "default": {},
    },
}

variants_file = {
    "path": {
        "type": "string",
        "check_with": validate_path,
        "coerce": "abspath",
        "required": True,
    },
    "format": {
        "type": "string",
        "allowed": ["dae", "vcf", "denovo", "cnv"],
        "required": True,
    },
    "params": {
        "type": "dict",
        "schema": {
            "add_chrom_prefix": {"type": "string"},
            "del_chrom_prefix": {"type": "string"},
            "dae_include_reference_genotypes": {"type": "boolean"},
            "denovo_location": {"type": "string"},
            "denovo_variant": {"type": "string"},
            "denovo_chrom": {"type": "string"},
            "denovo_pos": {"type": "string"},
            "denovo_ref": {"type": "string"},
            "denovo_alt": {"type": "string"},
            "denovo_person_id": {"type": "string"},
            "denovo_family_id": {"type": "string"},
            "denovo_best_state": {"type": "string"},
            "denovo_genotype": {"type": "string"},
            "denovo_sep": {"type": "string"},
            "vcf_include_reference_genotypes": {"type": "boolean"},
            "vcf_include_unknown_family_genotypes": {"type": "boolean"},
            "vcf_include_unknown_person_genotypes": {"type": "boolean"},
            "vcf_multi_loader_fill_in_mode": {"type": "string"},
            "vcf_denovo_mode": {"type": "string"},
            "vcf_omission_mode": {"type": "string"},
            "vcf_chromosomes": {"type": "string"},
            "vcf_pedigree_mode": {"type": "string"},
        },
        "default": {},
    },
}

genotype_storage_schema = {
    "id": {"type": "string"},
    "files": {
        "type": "dict",
        "schema": {
            "pedigree": {"type": "dict", "schema": family_schema},
            "variants": {
                "type": "list",
                "schema": {"type": "dict", "schema": variants_file},
                "default": [],
            },
        },
        "excludes": "tables",
    },
    "tables": {
        "type": "dict",
        "anyof_schema": [{
            "pedigree": {"type": "string"},
            "variants": {"type": "string"},
        }, {
            "pedigree": {"type": "string"},
            "summary": {"type": "string"},
            "family": {"type": "string"},
            "meta": {"type": "string"},
        }],
        "excludes": "files",
    },
}


study_config_schema = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "enabled": {"type": "boolean"},
    "work_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "default": ".",
    },
    "conf_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "default": ".",
        "required": True,
    },
    "phenotype_data": {"type": "string"},
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
    "has_denovo": {"type": "boolean", "default": True},
    "has_zygosity": {"type": "boolean", "default": False},
    "has_transmitted": {"type": "boolean"},
    "has_complex": {"type": "boolean"},
    "has_cnv": {"type": "boolean"},
    "has_tandem_repeat": {"type": "boolean"},
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
    "common_report": {
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
                "check_with": validate_path,
                "coerce": "abspath",
                "default": "common_report.json",
            },
        },
        "default": {"enabled": False},
    },
    "denovo_gene_sets": {
        "type": "dict",
        "schema": {
            "enabled": {"type": "boolean", "required": False},
            "selected_person_set_collections": {
                "type": "list",
                "schema": {"type": "string"},
            },
            "selected_standard_criterias_values": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "standard_criterias": {
                "type": "dict",
                "valuesrules": {
                    "type": "dict",
                    "schema": {
                        "segments": {
                            "type": "dict",
                            "valuesrules": {"type": "string"},
                        },
                    },
                },
                "default": {
                    "effect_types": {
                        "segments": {
                            "LGDs": "LGDs",
                            "Missense": "missense",
                            "Synonymous": "synonymous",
                        },
                    },
                    "sexes": {
                        "segments": {
                            "Female": "F",
                            "Male": "M",
                            "Unspecified": "U",
                        },
                    },
                },
            },
            "recurrency_criteria": {
                "type": "dict",
                "schema": {
                    "segments": {
                        "type": "dict",
                        "valuesrules": {
                            "type": "dict",
                            "schema": {
                                "start": {"type": "integer"},
                                "end": {"type": "integer"},
                            },
                        },
                    },
                },
                "default": {
                    "segments": {
                        "Single": {
                            "start": 1,
                            "end": 2,
                        },
                        "Triple": {
                            "start": 3,
                            "end": -1,
                        },
                        "Recurrent": {
                            "start": 2,
                            "end": -1,
                        },
                    },
                },
            },
            "gene_sets_names": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [
                    "LGDs", "LGDs.Male", "LGDs.Female",
                    "LGDs.Recurrent", "LGDs.Triple",
                    "Missense", "Missense.Male", "Missense.Female",
                    "Missense.Recurrent", "Missense.Triple",
                    "Synonymous", "Synonymous.Male", "Synonymous.Female",
                    "Synonymous.Recurrent", "Synonymous.Triple",
                ],
            },
        },
    },
    "enrichment": {
        "type": "dict",
        "schema": {
            "enabled": {"type": "boolean", "required": True},
            "selected_person_set_collections": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "selected_background_models": {
                "type": "list",
                "required": True,
                "schema": {"type": "string"},
                "default": [],
            },
            "default_background_model": {"type": "string"},
            "selected_counting_models": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "counting": {
                "type": "dict",
                "valuesrules": {"type": "dict", "schema": counting_schema},
                "default": counting_defaults,
            },
            "default_counting_model": {
                "type": "string",
                "default": "enrichment_events_counting",
            },
            "effect_types": {
                "type": "list",
                "schema": {"type": "string"},
                "default": ["LGDs", "missense", "synonymous"],
            },
        },
        "default": {"enabled": False},
    },
    "gene_browser": {
        "type": "dict",
        "schema": {
            "enabled": {"type": "boolean", "required": True},
            "frequency_column": {"type": "string", "required": True},
            "frequency_name": {"type": "string", "required": False},
            "effect_column": {"type": "string", "required": True},
            "location_column": {"type": "string", "required": True},
            "domain_min": {
                "type": "float",
                "required": True,
                "forbidden": [0.0],
                "min": 0.0,
                "max": 100.0,
            },
            "domain_max": {
                "type": "float",
                "required": True,
                "forbidden": [0.0],
                "min": 0.0,
                "max": 100.0,
            },
            "has_affected_status": {"type": "boolean", "default": True},
        },
    },
    "person_set_collections": person_set_collections_schema,
}
