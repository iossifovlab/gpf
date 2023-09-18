# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pytest
import yaml
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.study_config import study_config_schema
from dae.configuration.study_config_builder import StudyConfigBuilder


def test_study_with_study_filters_fails():
    study_config = {
        "id": "test",
        "genotype_browser": {
            "enabled": True,
            "has_study_filters": True
        },
    }
    with pytest.raises(ValueError) as err:
        GPFConfigParser.validate_config(
            study_config, study_config_schema, conf_dir=os.path.abspath(".")
        )
    print(err)


def test_dataset_with_study_filters_passes():
    study_config = {
        "id": "test",
        "studies": ["asdf"],
        "genotype_browser": {
            "enabled": True,
            "has_study_filters": True
        },
    }
    GPFConfigParser.validate_config(
        study_config, study_config_schema, conf_dir=os.path.abspath(".")
    )


def test_study_with_study_filters_false_passes():
    study_config = {
        "id": "test",
        "genotype_browser": {
            "enabled": True,
            "has_study_filters": False
        },
    }
    GPFConfigParser.validate_config(
        study_config, study_config_schema, conf_dir=os.path.abspath(".")
    )


@pytest.fixture
def full_study_config():
    return {
        "id": "test",
        "name": "test",
        "enabled": True,
        "work_dir": "test",
        "conf_dir": "test",
        "phenotype_data": "test",
        "phenotype_browser": True,
        "phenotype_tool": True,
        "description_editable": True, 
        "description_file": "test",
        "study_type": ["test"],
        "year": [1],
        "pub_med": ["test"],
        "genome": "test",
        "study_phenotype": "test",
        "chr_prefix": True,
        "has_denovo": True,
        "has_transmitted": True,
        "has_complex": True,
        "has_cnv": True,
        "has_tandem_repeat": True,
        "genotype_storage": {
            "id": "test",
            "files": {
                "pedigree": {
                    "path": "test",
                    "params": {
                        "ped_file": "test",
                        "ped_family": "test",
                        "ped_person": "test",
                        "ped_mom": "test",
                        "ped_dad": "test",
                        "ped_sex": "test",
                        "ped_status": "test",
                        "ped_role": "test",
                        "ped_no_role": True,
                        "ped_proband": "test",
                        "ped_no_header": True,
                        "ped_file_format": "test",
                        "ped_layout_mode": "test",
                        "ped_sep": "test",
                        "ped_tags": True,
                        "ped_no_tags": True,
                    }
                },
                "variants": [
                    {
                        "path": "test",
                        "format": "test",
                        "params": {
                            "add_chrom_prefix": "test",
                            "del_chrom_prefix": "test",
                            "dae_include_reference_genotypes": True,
                            "denovo_location": "test",
                            "denovo_variant": "test",
                            "denovo_chrom": "test",
                            "denovo_pos": "test",
                            "denovo_ref": "test",
                            "denovo_alt": "test",
                            "denovo_person_id": "test",
                            "denovo_family_id": "test",
                            "denovo_best_state": "test",
                            "denovo_genotype": "test",
                            "denovo_sep": "test",
                            "vcf_include_reference_genotypes": True,
                            "vcf_include_unknown_family_genotypes": True,
                            "vcf_include_unknown_person_genotypes": True,
                            "vcf_multi_loader_fill_in_mode": "test",
                            "vcf_denovo_mode": "test",
                            "vcf_omission_mode": "test",
                            "vcf_chromosomes": "test",
                            "vcf_pedigree_mode": "test"
                        },
                    }
                ],
            },
            "tables": {
                "pedigree": "test",
                "variants": "test",
            }
        },
        "studies": ["test"],
        "genotype_browser": {
            "enabled": True,
            "has_family_filters": True,
            "has_family_structure_filter": True,
            "has_person_filters": True,
            "has_study_filters": True,
            "has_present_in_child": True,
            "has_present_in_parent": True,
            "has_pedigree_selector": True,
            "has_study_types": True,
            "has_graphical_preview": True,
            "show_all_unknown": True,
            "inheritance_type_filter": ["test"],
            "selected_inheritance_type_filter_values": ["list"],
            "columns": {
                "genotype": {
                    "test": {
                        "name": "test",
                        "source": "test",
                        "format": "test",
                    }
                },
                "phenotype": {
                    "test": {
                        "name": "test",
                        "source": "test",
                        "format": "test",
                        "role": "test",
                    }
                },
            },
            "column_groups": {
                "test": {
                    "name": "test",
                    "columns": ["test"]
                }
            },
            "preview_columns": ["test"],
            "download_columns": ["test"],
            "preview_columns_ext": ["test"],
            "download_columns_ext": ["test"],
            "summary_preview_columns": ["test"],
            "summary_download_columns": ["test"],
            "person_filters": {
                "test": {
                    "name": "test",
                    "from": "test",
                    "source": "test",
                    "source_type": "test",
                    "filter_type": "test",
                }
            },
            "family_filters": {
                "test": {
                    "name": "test",
                    "from": "test",
                    "source": "test",
                    "source_type": "test",
                    "filter_type": "test",
                    "role": "test"
                }
            },
            "variant_types": ["test"],
            "selected_variant_types": ["test"],
            "max_variants_count": 1000
        },
        "common_report": {
            "enabled": True,
            "selected_person_set_collections": {
                "denovo_report": ["test"],
                "family_report": ["test"],
            },
            "effect_groups": ["test"],
            "effect_types": ["test"],
            "draw_all_families": True,
            "file_path": "test"
        },
        "denovo_gene_sets": {
            "enabled": True,
            "selected_person_set_collections": ["test"],
            "selected_standard_criterias_values": ["test"],
            "standard_criterias": {
                "test": {"segments": {"test": "test"}}
            },
            "recurrency_criteria": {
                "segments": {
                    "test": {
                        "start": 1,
                        "end": 1
                    }
                }
            },
            "gene_sets_names": ["test"]
        },
        "enrichment": {
            "enabled": True,
            "selected_person_set_collections": ["test"],
            "selected_background_values": ["test"],
            "background": {
                "test": {
                    "file": "test",
                    "name": "test",
                    "kind": "test",
                    "desc": "test"
                }
            },
            "default_background_model": "test",
            "selected_counting_values": ["test"],
            "counting": {
                "test": {
                    "name": "test",
                    "desc": "test"
                }
            },
            "default_counting_model": "test",
            "effect_types": ["test"]
        },
        "gene_browser": {
            "enabled": True,
            "frequency_column": "test",
            "frequency_name": "test",
            "effect_column": "test",
            "location_column": "test",
            "domain_min": 1.0,
            "domain_max": 1.0,
            "has_affected_status": True
        },
        "person_set_collections": {
            "test1": ["test"],
            "test2": {
                "id": "test",
                "name": "test",
                "sources": [
                    {
                        "from": "test",
                        "source": "test"
                    }
                ],
                "domain": [
                    {
                        "id": "test",
                        "name": "test",
                        "values": ["test"],
                        "color": "test"
                    }
                ],
                "default": {
                    "id": "test",
                    "name": "test",
                    "values": ["test"],
                    "color": "test"
                }
            }
        }
    }


def _build_structural_schema_value(output_schema, input_schema):
    for k, v in input_schema.items():
        if k not in ["type", "schema", "valuesrules", "anyof_schema"]:
            continue

        if k == "type":
            output_schema[k] = v

        if k == "valuesrules":
            output_schema[k] = _build_structural_schema_value(
                {}, input_schema[k]
            )

        if k == "anyof_schema":
            output_schema[k] = []
            for schema in input_schema[k]:
                output_schema[k].append(
                    _build_structural_schema_keys({}, schema)
                )

        if k == "oneof":
            output_schema[k] = []
            for schema in input_schema[k]:
                output_schema[k].append(
                    _build_structural_schema_value({}, schema)
                )

    if output_schema.get("type") == "list":
        output_schema["schema"] = _build_structural_schema_value(
            {}, input_schema["schema"]
        )
    elif output_schema.get("type") == "dict" and \
            "valuesrules" not in output_schema and \
            "anyof_schema" not in output_schema:
        output_schema["schema"] = _build_structural_schema_keys(
            {}, input_schema["schema"]
        )
    output_schema["required"] = True
    return output_schema


def _build_structural_schema_keys(output_schema, input_schema):
    for k, v in input_schema.items():
        output_schema[k] = _build_structural_schema_value(
            {}, v
        )
    return output_schema


def build_structural_schema(schema):
    return _build_structural_schema_keys({}, schema)


@pytest.fixture()
def study_config_structural():
    return build_structural_schema(study_config_schema)


def test_structural_config_generation():
    schema = {
        "field1": {"type": "string"},
        "field2": {"type": "string", "dependencies": "field1"},
        "field3": {"type": "string", "excludes": "field1"}
    }

    temp = {"field1": "asdf", "field2": "ghjk"}

    assert GPFConfigParser.validate_config(temp, schema)

    temp = {"field2": "ghjk"}

    with pytest.raises(ValueError):
        GPFConfigParser.validate_config(temp, schema)
        temp = {"field1": "asdf", "field3": "ghjk"}
        GPFConfigParser.validate_config(temp, schema)

    temp = {"field1": "asdf", "field2": "ghjk"}

    structural_schema = build_structural_schema(schema)

    with pytest.raises(ValueError):
        GPFConfigParser.validate_config(temp, structural_schema)

    temp["field3"] = "zxc"

    GPFConfigParser.validate_config(temp, structural_schema)

    temp["field4"] = "asdf"

    with pytest.raises(ValueError):
        GPFConfigParser.validate_config(temp, structural_schema)


def test_study_config_structure(full_study_config, study_config_structural):
    GPFConfigParser.validate_config(full_study_config, study_config_structural)


def test_study_config_builder(full_study_config, study_config_structural):
    builder = StudyConfigBuilder(full_study_config)
    config = builder.build_config()
    read_config = yaml.safe_load(config)
    GPFConfigParser.validate_config(read_config, study_config_structural)
