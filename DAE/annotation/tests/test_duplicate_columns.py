import pytest
from box import Box
from collections import OrderedDict

from annotation.tools.duplicate_columns import\
    DuplicateColumnsAnnotator


@pytest.fixture
def duplicate_columns():
    config = Box(OrderedDict([('columns', 'CSHL:location,CSHL:variant'),
                              ('labels', 'location,variant')]),
                 default_box=True, default_box_attr=None)
    columns_reverse_config = Box(
        OrderedDict([('columns', 'CSHL:variant,CSHL:location'),
                     ('labels', 'variant,location')]),
        default_box=True, default_box_attr=None)
    columns_with_index = Box(
        OrderedDict([('columns', '2,3'),
                     ('labels', 'l,v')]),
        default_box=True, default_box_attr=None)

    return (DuplicateColumnsAnnotator(
            config,
            ['familyId', 'CSHL:location', 'CSHL:variant']),
            DuplicateColumnsAnnotator(
            columns_reverse_config,
            ['familyId', 'CSHL:location', 'CSHL:variant']),
            DuplicateColumnsAnnotator(columns_with_index))


def test_new_columns(duplicate_columns):
    new_columns = duplicate_columns[0].new_columns
    new_columns_reverse = duplicate_columns[1].new_columns
    new_columns_with_index = duplicate_columns[2].new_columns

    assert new_columns == ['CSHL:location', 'CSHL:variant']
    assert new_columns_reverse == ['CSHL:variant', 'CSHL:location']
    assert new_columns_with_index == ['2', '3']


def test_line_annotations(duplicate_columns):
    line = ['1-1111-111', '1:1111111', 'ins(A)']
    columns = ['CSHL:location', 'CSHL:variant']
    new_values = duplicate_columns[0].line_annotations(line, columns)

    line_reverse = ['1-1111-111', '1:1111111', 'ins(A)']
    columns_reverse = ['CSHL:variant', 'CSHL:location']
    new_values_reverse = duplicate_columns[1].line_annotations(line_reverse,
                                                               columns_reverse)

    line_with_index = ['1-1111-111', '1:1111111', 'ins(A)']
    columns_with_index = ['2', '3']
    new_values_with_index =\
        duplicate_columns[2].line_annotations(line_with_index,
                                              columns_with_index)

    assert new_values == ['1:1111111', 'ins(A)']
    assert new_values_reverse == ['ins(A)', '1:1111111']
    assert new_values_with_index == ['1:1111111', 'ins(A)']
