'''
Created on Aug 12, 2016

@author: lubo
'''


def set_variable_descriptor_from_main_row(vd, row):
    vd.table_name = row['tableName']
    vd.unique_variable_name = row['name']
    vd.variable_id = row['variableId']
    vd.domain = row['domain']
    vd.domain_choice_label = row['domainChoiceLabel']
    vd.measurement_scale = row['measurementScale']
    vd.regards_mother = row['regardsMother']
    vd.regards_father = row['regardsFather']
    vd.regards_proband = row['regardsProband']
    vd.regards_sibling = row['regardsSibling']
    vd.regards_family = row['regardsFamily']
    vd.regards_other = row['regardsOther']
    vd.is_calculated = False

    vd.variable_notes = \
        str(row['variableNotes']) + '\n' + \
        str(row['questionInstruction'])


def set_variable_descriptor_from_ssc_row(vd, row):
    vd.table_name = row['tableName']
    vd.variable_category = row['variableCategory']
    vd.unique_variable_name = row['name']
    vd.variable_id = row['variableId']
    vd.domain = row['domain']
    vd.domain_choice_label = row['domainChoiceLabel']
    vd.measurement_scale = row['measurementScale']

    vd.is_calculated = row['isCalculated']
    vd.calculation_documentation = row['calculationDocumentation']

    if row['variableNotes']:
        vd.variable_notes = row['variableNotes']
