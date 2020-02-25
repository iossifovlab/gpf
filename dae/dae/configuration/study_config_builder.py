from typing import Dict, Any
from jinja2 import Template
from collections import UserDict, UserList


class StudyConfigBuilder:
    def __init__(self, config_dict: Dict[str, Any]):
        assert config_dict
        assert config_dict["genotype_storage"]
        self._config_dict = TOMLDict.from_dict(config_dict)

    def build_config(self) -> str:
        return STUDY_CONFIG_TEMPLATE.render(self._config_dict)


class TOMLDict(UserDict):
    @staticmethod
    def from_dict(input_dict):
        output = TOMLDict(input_dict)
        for k, v in output.items():
            if isinstance(v, dict):
                output[k] = TOMLDict.from_dict(v)
            elif isinstance(v, list):
                output[k] = TOMLList.from_list(v)
            elif isinstance(v, bool):
                output[k] = "true" if v else "false"
        return output

    def _get_val_str(self, val):
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
    @staticmethod
    def from_list(input_list):
        output = TOMLList(input_list)
        for idx, el in enumerate(output):
            if isinstance(el, dict):
                output[idx] = TOMLDict.from_dict(el)
            elif isinstance(el, list):
                output[idx] = TOMLList.from_list(el)
            elif isinstance(el, bool):
                output[idx] = "true" if el else "false"
        return output

    def _get_val_str(self, val):
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
        for el in self:
            if not first:
                output += ", "

            output += f"{self._get_val_str(el)}"
            first = False

        output += "]"
        return output


STUDY_CONFIG_TEMPLATE = Template("""\
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

{%- if selected_people_groups %}
selected_people_groups = "{{ selected_people_groups }}"
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
pedigree.params = {{ genotype_storage.files.pedigree.params }}
{% for variant in genotype_storage.files.variants %}
[[genotype_storage.files.variants]]
path = "{{ variant.path }}"
format = "{{ variant.format }}"
params = {{ variant.params }}
{% endfor %}
{% endif %}

{%- if people_group %}
[people_group]
{% for key, value in people_group.items() %}
{%- if value is mapping -%}
{{key}}.id = "{{ value.id }}"
{{key}}.name = "{{ value.name }}"
{{key}}.domain = {{ value.domain }}
{{key}}.default = {{ value.default }}
{{key}}.source = "{{ value.source }}"
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

{%- if genotype_browser.has_cnv %}
has_cnv = {{ genotype_browser.has_cnv }}
{%- endif %}

{%- if genotype_browser.has_complex %}
has_complex = {{ genotype_browser.has_complex }}
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

{%- if genotype_browser.selected_in_roles_values %}
selected_in_roles_values = "{{ genotype_browser.selected_in_roles_values }}"
{%- endif %}

{%- if genotype_browser.inheritance_type_filter %}
inheritance_type_filter = "{{ genotype_browser.inheritance_type_filter }}"
{%- endif %}

{%- if genotype_browser.selected_inheritance_type_filter_values %}
selected_inheritance_type_filter_values =\
"{{ genotype_browser.selected_inheritance_type_filter_values }}"
{%- endif %}

{%- if genotype_browser.in_roles %}
{%- for k, v in genotype_browser.in_roles.items() %}
in_roles.{{ k }}.destination = "{{ v.destination }}"
in_roles.{{ k }}.roles = {{ v.roles }}
{%- endfor %}
{%- endif %}

{%- if genotype_browser.genotype %}
{%- for k, v in genotype_browser.genotype.items() %}
genotype.{{ k }}.name = "{{ v.name }}"
{%- if v.source %}
genotype.{{ k }}.source = "{{ v.source }}"
{%- endif %}

{%- if v.slots %}
genotype.{{ k }}.slots = "{{ v.slots }}"
{%- endif %}
{%- endfor %}
{%- endif %}


{%- if genotype_browser.pheno %}
{%- for k, v in genotype_browser.pheno.items() %}
pheno.{{ k }}.name = "{{ v.name }}"
{%- if v.source %}
pheno.{{ k }}.source = "{{ v.source }}"
{%- endif %}

{%- if v.slots %}
pheno.{{ k }}.slots = "{{ v.slots }}"
{%- endif %}
{%- endfor %}
{%- endif %}

{%- if genotype_browser.selected_genotype_column_values %}
selected_genotype_column_values = \
"{{ genotype_browser.selected_genotype_column_values }}"
{%- endif %}

{%- if genotype_browser.preview_columns %}
preview_columns = "{{ genotype_browser.preview_columns }}"
{%- endif %}

{%- if genotype_browser.download_columns %}
download_columns = "{{ genotype_browser.download_columns }}"
{%- endif %}


{%- if genotype_browser.present_in_role %}
present_in_role = "{{ genotype_browser.present_in_role }}"
{%- endif %}

{%- if genotype_browser.pheno_filters %}
pheno_filters = "{{ genotype_browser.pheno_filters }}"
{%- endif %}

{%- if genotype_browser.selected_pheno_filters_values %}
selected_pheno_filters_values = \
"{{ genotype_browser.selected_pheno_filters_values }}"
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
effect_groups = "{{ common_report.effect_groups }}"
{%- endif %}

{%- if common_report.effect_types %}
effect_types = "{{ common_report.effect_types }}"
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

{%- if denovo_gene_sets.selected_people_groups %}
selected_people_groups = "{{ denovo_gene_sets.selected_people_groups }}"
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

""")
