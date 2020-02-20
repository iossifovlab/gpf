from typing import Dict, Any
from dae.configuration.gpf_config_parser import GPFConfigValidator
from dae.configuration.schemas.study_config import study_config_schema


class StudyConfigBuilder:
    def __init__(self, config_dict: Dict[str, Any], config_dir: str):
        assert config_dict
        assert config_dict["genotype_storage"]
        self._config_dict = config_dict
        self._config_dir = config_dir
        self.is_impala = "tables" in config_dict["genotype_storage"]

    def build_config(self) -> str:
        validator = GPFConfigValidator(
            study_config_schema, conf_dir=self._config_dir
        )
        assert validator.validate(self._config_dict), validator.errors
        storage_data = (
            self.build_storage_data_impala()
            if self.is_impala
            else self.build_storage_data_filesystem()
        )
        gt_browser_enabled = self._config_dict["genotype_browser"]["enabled"]
        return STUDY_CONFIG_TEMPLATE.format(
            study_id=self._config_dict["id"],
            genotype_storage=self._config_dict["genotype_storage"]["id"],
            storage_data=storage_data,
            has_denovo="true" if self._config_dict["has_denovo"] else "false",
            genotype_browser_enabled="true" if gt_browser_enabled else "false"
        )

    def build_storage_data_impala(self) -> str:
        tables = self._config_dict["genotype_storage"]["tables"]
        if "variants" in tables:
            variants = f'variants = "{tables["variants"]}"'
        else:
            variants = ""
        return STUDY_IMPALA_CONFIG_TEMPLATE.format(
            pedigree_table=tables["pedigree"], variants=variants
        )

    def build_storage_data_filesystem(self) -> str:
        variants_list = self._config_dict["genotype_storage"]["files"][
            "variants"
        ]
        variants_sections = []
        for variants in variants_list:
            params = (
                "{"
                + ", ".join(
                    [
                        '{} = "{}"'.format(k, str(v).replace("\t", "\\t"))
                        for k, v in variants["params"].items()
                    ]
                )
                + "}"
            )
            section = STUDY_VARIANTS_TEMPLATE.format(
                path=variants["path"], format=variants["format"], params=params
            )
            variants_sections.append(section)

        pedigree = self._config_dict["genotype_storage"]["files"]["pedigree"]
        pedigree_params = (
            "{"
            + ", ".join(
                [
                    '{} = "{}"'.format(k, str(v).replace("\t", "\\t"))
                    for k, v in pedigree["params"].items()
                ]
            )
            + "}"
        )
        return STUDY_FILESYSTEM_CONFIG_TEMPLATE.format(
            path=pedigree["path"],
            params=pedigree_params,
            variants="\n\n".join(variants_sections),
        )


STUDY_VARIANTS_TEMPLATE = """
[[genotype_storage.files.variants]]
path = "{path}"
format = "{format}"
params = {params}
"""

STUDY_FILESYSTEM_CONFIG_TEMPLATE = """
[genotype_storage.files]
pedigree.path = "{path}"
pedigree.params = {params}

{variants}
"""

STUDY_IMPALA_VARIANTS_TEMPLATE = """
variants = "{variant_table}"
"""

STUDY_IMPALA_CONFIG_TEMPLATE = """
[genotype_storage.tables]
pedigree = "{pedigree_table}"
{variants}
"""

STUDY_CONFIG_TEMPLATE = """
id = "{study_id}"
conf_dir = "."
has_denovo = {has_denovo}
[genotype_storage]
id = "{genotype_storage}"

{storage_data}
[genotype_browser]
enabled = {genotype_browser_enabled}
"""
