from collections import UserDict, UserList
import typing
from typing import Dict, Any
import yaml

from jinja2 import Template


class ConfigDumper(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


class StudyConfigBuilder:
    """Class used for building study configurations from dictionaries."""

    def __init__(self, config_dict: Dict[str, Any]):
        assert config_dict
        assert config_dict["genotype_storage"]
        self._config_dict = self._cleanup_dict(config_dict)

    @classmethod
    def _cleanup_dict(cls, config_dict):
        for k, v in list(config_dict.items()):
            print(k, v)
            if v is None:
                print("deleting")
                print(config_dict)
                del config_dict[k]
                print(config_dict)

            elif isinstance(v, dict):
                config_dict[k] = cls._cleanup_dict(v)
            elif isinstance(v, list):
                for idx, elem in enumerate(v):
                    if isinstance(elem, dict):
                        v[idx] = cls._cleanup_dict(elem)
        return config_dict

    def build_config(self) -> str:
        print(self._config_dict)
        return typing.cast(str, yaml.dump(
            self._config_dict,
            default_flow_style=False,
            sort_keys=False,
            Dumper=ConfigDumper
        ))


class TOMLDict(UserDict):
    """Class that transforms Python dictionaries to TOML dictionaries."""

    @staticmethod
    def from_dict(input_dict):
        """
        Construct TOMLDict from a Python dictionary.

        Any dictionaries or lists in the dictionary's
        values are also converted.
        """
        output = TOMLDict(input_dict)
        for k, v in output.items():
            if isinstance(v, dict):
                output[k] = TOMLDict.from_dict(v)
            elif isinstance(v, list):
                output[k] = TOMLList.from_list(v)
            elif isinstance(v, bool):
                output[k] = "true" if v else "false"
        return output

    @staticmethod
    def _get_val_str(val):
        if isinstance(val, str):
            output = f'"{val}"'
        elif isinstance(val, bool):
            output = "true" if val else "false"
        else:
            output = str(val)
        return output

    def __str__(self):
        if len(self) == 0:
            return "{}"
        output = "{ "
        first = True
        for k, v in self.items():
            if not first:
                output += ", "

            output += f"{k} = {self._get_val_str(v)}"
            first = False

        output += " }"
        return output


class TOMLList(UserList):
    """Class that transforms Python dictionaries to TOML dictionaries."""

    @staticmethod
    def from_list(input_list):
        """
        Construct TOMLList from a Python list.

        Any dictionaries or lists in the list's
        element are also converted.
        """
        output = TOMLList(input_list)
        for idx, element in enumerate(output):
            if isinstance(element, dict):
                output[idx] = TOMLDict.from_dict(element)
            elif isinstance(element, list):
                output[idx] = TOMLList.from_list(element)
            elif isinstance(element, bool):
                output[idx] = "true" if element else "false"
        return output

    @staticmethod
    def _get_val_str(val):
        if isinstance(val, str):
            output = f'"{val}"'
        elif isinstance(val, bool):
            output = "true" if val else "false"
        else:
            output = str(val)
        return output

    def __str__(self):
        if len(self) == 0:
            return "[]"
        output = "["
        first = True
        for element in self:
            if not first:
                output += ", "

            output += f"{self._get_val_str(element)}"
            first = False

        output += "]"
        return output


STUDY_CONFIG_TEMPLATE = Template(
    """\
id = "{{ id }}"

{%- if name %}
name = "{{ name }}"
{%- endif %}

{%- if work_dir %}
work_dir = "{{ work_dir }}"
{%- endif %}\

conf_dir = "."

{%- if phenotype_data %}
phenotype_data = "{{ phenotype_data }}"
{%- endif %}

{%- if phenotype_browser %}
phenotype_browser = {{ phenotype_browser }}
{%- endif %}

{%- if phenotype_tool %}
phenotype_tool = {{ phenotype_tool }}
{%- endif %}

{%- if description %}
description = "{{ description }}"
{%- endif %}

{%- if description_file %}
description_file = "{{ description_file }}"
{%- endif %}

{%- if selected_person_set_collections %}
selected_person_set_collections = "{{ selected_person_set_collections }}"
{%- endif %}

{%- if study_type %}
study_type = {{ study_type }}
{%- endif %}

{%- if year %}
year = {{ year }}
{%- endif %}

{%- if pub_med %}
pub_med = {{ pub_med }}
{%- endif %}\

has_denovo = {{ has_denovo }}

{%- if has_transmitted %}
has_transmitted = {{ has_transmitted }}
{%- endif %}

{%- if has_complex %}
has_complex = {{ has_complex }}
{%- endif %}

{%- if has_cnv %}
has_cnv = {{ has_cnv }}
{%- endif %}

{%- if studies %}
studies = {{ studies }}
{%- endif %}

[genotype_storage]
id = "{{ genotype_storage.id }}"
{% if genotype_storage.tables %}
[genotype_storage.tables]
pedigree = "{{ genotype_storage.tables.pedigree }}"
{%- if genotype_storage.tables.variants %}
variants = "{{ genotype_storage.tables.variants }}"
{%- endif %}
{% elif genotype_storage.files %}
[genotype_storage.files]
pedigree.path = "{{ genotype_storage.files.pedigree.path }}"
{%- if genotype_storage.files.pedigree.params %}


{%- if genotype_storage.files.pedigree.params.ped_family %}
pedigree.params.ped_family = \
"{{ genotype_storage.files.pedigree.params.ped_family }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_person %}
pedigree.params.ped_person = \
"{{ genotype_storage.files.pedigree.params.ped_person }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_mom %}
pedigree.params.ped_mom = \
"{{ genotype_storage.files.pedigree.params.ped_mom }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_dad %}
pedigree.params.ped_dad = \
"{{ genotype_storage.files.pedigree.params.ped_dad }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_sex %}
pedigree.params.ped_sex = \
"{{ genotype_storage.files.pedigree.params.ped_sex }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_status %}
pedigree.params.ped_status = \
"{{ genotype_storage.files.pedigree.params.ped_status }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_role %}
pedigree.params.ped_role = \
"{{ genotype_storage.files.pedigree.params.ped_role }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_no_role %}
pedigree.params.ped_no_role = \
"{{ genotype_storage.files.pedigree.params.ped_no_role }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_proband %}
pedigree.params.ped_proband = \
"{{ genotype_storage.files.pedigree.params.ped_proband }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_no_header %}
pedigree.params.ped_no_header = \
"{{ genotype_storage.files.pedigree.params.ped_no_header }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_file_format %}
pedigree.params.ped_file_format = \
"{{ genotype_storage.files.pedigree.params.ped_file_format }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_layout_mode %}
pedigree.params.ped_layout_mode = \
"{{ genotype_storage.files.pedigree.params.ped_layout_mode }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_sep %}
pedigree.params.ped_sep = \
"{{ genotype_storage.files.pedigree.params.ped_sep }}"
{%- endif %}

{%- if genotype_storage.files.pedigree.params.ped_tags %}
pedigree.params.ped_tags = \
{{ genotype_storage.files.pedigree.params.ped_tags }}
{%- endif %}

{%- else %}
pedigree.params = {}
{%- endif %}
{% for variant in genotype_storage.files.variants %}
[[genotype_storage.files.variants]]
path = "{{ variant.path }}"
format = "{{ variant.format }}"
{%- if variant.params %}

{%- if variant.params.add_chrom_prefix %}
params.add_chrom_prefix = "{{ variant.params.add_chrom_prefix }}"
{%- endif %}
{%- if variant.params.del_chrom_prefix %}
params.del_chrom_prefix = "{{ variant.params.del_chrom_prefix }}"
{%- endif %}
{%- if variant.params.dae_include_reference_genotypes %}
params.dae_include_reference_genotypes = \
{{ variant.params.dae_include_reference_genotypes }}
{%- endif %}
{%- if variant.params.denovo_location %}
params.denovo_location = "{{ variant.params.denovo_location }}"
{%- endif %}
{%- if variant.params.denovo_variant %}
params.denovo_variant = "{{ variant.params.denovo_variant }}"
{%- endif %}
{%- if variant.params.denovo_chrom %}
params.denovo_chrom = "{{ variant.params.denovo_chrom }}"
{%- endif %}
{%- if variant.params.denovo_pos %}
params.denovo_pos = "{{ variant.params.denovo_pos }}"
{%- endif %}
{%- if variant.params.denovo_ref %}
params.denovo_ref = "{{ variant.params.denovo_ref }}"
{%- endif %}
{%- if variant.params.denovo_alt %}
params.denovo_alt = "{{ variant.params.denovo_alt }}"
{%- endif %}
{%- if variant.params.denovo_person_id %}
params.denovo_person_id = "{{ variant.params.denovo_person_id }}"
{%- endif %}
{%- if variant.params.denovo_family_id %}
params.denovo_family_id = "{{ variant.params.denovo_family_id }}"
{%- endif %}
{%- if variant.params.denovo_best_state %}
params.denovo_best_state = "{{ variant.params.denovo_best_state }}"
{%- endif %}
{%- if variant.params.denovo_genotype %}
params.denovo_genotype = "{{ variant.params.denovo_genotype }}"
{%- endif %}
{%- if variant.params.denovo_sep %}
params.denovo_sep = "{{ variant.params.denovo_sep }}"
{%- endif %}
{%- if variant.params.vcf_include_reference_genotypes %}
params.vcf_include_reference_genotypes = \
{{ variant.params.vcf_include_reference_genotypes }}
{%- endif %}
{%- if variant.params.vcf_include_unknown_family_genotypes %}
params.vcf_include_unknown_family_genotypes = \
{{ variant.params.vcf_include_unknown_family_genotypes }}
{%- endif %}
{%- if variant.params.vcf_include_unknown_person_genotypes %}
params.vcf_include_unknown_person_genotypes = \
{{ variant.params.vcf_include_unknown_person_genotypes }}
{%- endif %}
{%- if variant.params.vcf_multi_loader_fill_in_mode %}
params.vcf_multi_loader_fill_in_mode = \
"{{ variant.params.vcf_multi_loader_fill_in_mode }}"
{%- endif %}
{%- if variant.params.vcf_denovo_mode %}
params.vcf_denovo_mode = "{{ variant.params.vcf_denovo_mode }}"
{%- endif %}
{%- if variant.params.vcf_omission_mode %}
params.vcf_omission_mode = "{{ variant.params.vcf_omission_mode }}"
{%- endif %}
{%- if variant.params.vcf_chromosomes %}
params.vcf_chromosomes = "{{ variant.params.vcf_chromosomes }}"
{%- endif %}

{%- else %}
params = {}
{%- endif %}
{% endfor %}
{%- endif %}

{%- if person_set_collections %}
[person_set_collections]
{% for key, value in person_set_collections.items() %}
{%- if value is mapping -%}
{{key}}.id = "{{ value.id }}"
{{key}}.name = "{{ value.name }}"
{{key}}.domain = {{ value.domain }}
{{key}}.default = {{ value.default }}
{{key}}.sources = "{{ value.sources }}"
{% else %}
{{ key }} = {{ value }}
{% endif %}
{%- endfor %}
{%- endif %}


{%- if genotype_browser %}
[genotype_browser]
{%- if genotype_browser.enabled %}
enabled = {{ genotype_browser.enabled }}
{%- endif %}

{%- if genotype_browser.has_family_filters %}
has_family_filters = {{ genotype_browser.has_family_filters }}
{%- endif %}

{%- if genotype_browser.has_study_filters %}
has_study_filters = {{ genotype_browser.has_study_filters }}
{%- endif %}

{%- if genotype_browser.has_present_in_child %}
has_present_in_child = {{ genotype_browser.has_present_in_child }}
{%- endif %}

{%- if genotype_browser.has_present_in_parent %}
has_present_in_parent = {{ genotype_browser.has_present_in_parent }}
{%- endif %}

{%- if genotype_browser.has_pedigree_selector %}
has_pedigree_selector = {{ genotype_browser.has_pedigree_selector }}
{%- endif %}

{%- if genotype_browser.has_study_types %}
has_study_types = {{ genotype_browser.has_study_types }}
{%- endif %}

{%- if genotype_browser.has_graphical_preview %}
has_graphical_preview = {{ genotype_browser.has_graphical_preview }}
{%- endif %}

{%- if genotype_browser.family_filters %}
family_filters = {{ genotype_browser.family_filters }}
{%- endif %}

{%- if genotype_browser.inheritance_type_filter %}
inheritance_type_filter = "{{ genotype_browser.inheritance_type_filter }}"
{%- endif %}

{%- if genotype_browser.selected_inheritance_type_filter_values %}
selected_inheritance_type_filter_values =\
"{{ genotype_browser.selected_inheritance_type_filter_values }}"
{%- endif %}

{%- if genotype_browser.variant_types %}
variant_types = {{ genotype_browser.variant_types }}
{%- endif %}

{%- if genotype_browser.selected_variant_types %}
selected_variant_types = {{ genotype_browser.selected_variant_types }}
{%- endif %}

{%- if genotype_browser.preview_columns %}
preview_columns = {{ genotype_browser.preview_columns }}
{%- endif %}

{%- if genotype_browser.download_columns %}
download_columns = {{ genotype_browser.download_columns }}
{%- endif %}

{%- if genotype_browser.summary_preview_columns %}
summary_preview_columns = {{ genotype_browser.summary_preview_columns }}
{%- endif %}

{%- if genotype_browser.summary_download_columns %}
summary_download_columns = {{ genotype_browser.summary_download_columns }}
{%- endif %}

{%- if genotype_browser.person_filters %}
person_filters = {{ genotype_browser.person_filters }}
{%- endif %}

{%- if genotype_browser.family_filters %}
family_filters = {{ genotype_browser.family_filters }}
{%- endif %}

{%- if genotype_browser.columns %}
{%- if genotype_browser.columns.genotype %}
[genotype_browser.columns.genotype]
{%- for k, v in genotype_browser.columns.genotype.items() %}
{{ k }}.name = "{{ v.name }}"
{{ k }}.source = "{{ v.source }}"
{%- if v.format %}
{{ k }}.format = "{{ v.format }}"
{%- endif %}
{%- endfor %}
{%- endif %}

{%- if genotype_browser.columns.phenotype %}
[genotype_browser.columns.phenotype]
{%- for k, v in genotype_browser.columns.phenotype.items() %}
{{ k }}.name = "{{ v.name }}"
{{ k }}.source = "{{ v.source }}"
{{ k }}.role = "{{ v.role }}"
{%- if v.format %}
{{ k }}.format = "{{ v.format }}"
{%- endif %}
{%- endfor %}
{%- endif %}
{%- endif %}

{%- if genotype_browser.column_groups %}
[genotype_browser.column_groups]
{%- for k, v in genotype_browser.column_groups.items() %}
{{ k }}.name = "{{ v.name }}"
{{ k }}.columns = {{ v.columns }}
{%- endfor %}
{%- endif %}

{%- endif %}

{%- if common_report %}
[common_report]

{%- if common_report.enabled %}
enabled = {{ common_report.enabled }}
{%- endif %}

{%- if common_report.groups %}
groups = "{{ common_report.groups }}"
{%- endif %}

{%- if common_report.effect_groups %}
effect_groups = {{ common_report.effect_groups }}
{%- endif %}

{%- if common_report.effect_types %}
effect_types = {{ common_report.effect_types }}
{%- endif %}

{%- if common_report.families_count_show_id %}
families_count_show_id = {{ common_report.families_count_show_id }}
{%- endif %}

{%- if common_report.draw_all_families %}
draw_all_families = {{ common_report.draw_all_families }}
{%- endif %}

{%- if common_report.file_path %}
file_path = "{{ common_report.file_path }}"
{%- endif %}

{%- endif %}


{%- if denovo_gene_sets %}
[denovo_gene_sets]

{%- if denovo_gene_sets.enabled %}
enabled = {{ denovo_gene_sets.enabled }}
{%- endif %}

{%- if denovo_gene_sets.selected_person_set_collections %}
selected_person_set_collections = \
"{{ denovo_gene_sets.selected_person_set_collections }}"
{%- endif %}

{%- if denovo_gene_sets.selected_standard_criterias_values %}
selected_standard_criterias_values = \
"{{ denovo_gene_sets.selected_standard_criterias_values }}"
{%- endif %}

{%- if denovo_gene_sets.standard_criteria %}
{%- for k, v in denovo_gene_sets.standard_criterias.items() %}
standard_criteria.{{ k }}.segments = {{ v.segments }}
{%- endfor %}
{%- endif %}


{%- if denovo_gene_sets.recurrency_criteria %}
{%- for k, v in denovo_gene_sets.recurrency_criteria.items() %}
recurrency_criteria.segments.{{ k }} = {{ v }}
{%- endfor %}
{%- endif %}


{%- if denovo_gene_sets.gene_sets_names %}
gene_sets_names = "{{ denovo_gene_sets.gene_sets_names }}"
{%- endif %}

{%- endif %}

"""
)
