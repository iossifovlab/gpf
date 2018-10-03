from __future__ import unicode_literals
import pytest
from box import Box
from collections import OrderedDict
from annotation.tools.change_coordinate_base import CoordinateBaseAnnotator

@pytest.fixture
def change_coord_base():
    config = Box(OrderedDict([("position","START"), ("to_one_base",False)]),default_box=True, default_box_attr=None)
    config_to1 = Box(OrderedDict([("position","START"), ("to_one_base",True), ("label","new_pos_b1")]), default_box=True, default_box_attr=None)
    
    return (CoordinateBaseAnnotator(config, ["START"]), CoordinateBaseAnnotator(config_to1, ["START"]))

def test_line_annotations(change_coord_base):
    line = ["4567890"]
    new_line = change_coord_base[0].line_annotations(line, change_coord_base[0].new_columns)
    line_2 = ["4949323"]
    new_line2 = change_coord_base[1].line_annotations(line_2, change_coord_base[1].new_columns)

    assert new_line == ["4567889"]
    assert new_line2 == ["4949324"]
