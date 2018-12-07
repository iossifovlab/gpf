from unittest.mock import patch

from pedigrees.layout_saver import LayoutSaver
import pedigrees.layout_saver


def test_member_key():
    assert LayoutSaver._member_key('fam_id', 'ind_id') == 'fam_id;ind_id'


def test_writerow_error(
        layout_saver, family1, error_message, people_with_layout_error,
        people1):
    layout_saver.writerow_error(family1, error_message)

    assert layout_saver._people_with_layout == people_with_layout_error
    assert layout_saver._people == people1


def test_writerow(layout_saver, family2, layout2, people_with_layout, people2):
    layout_saver.writerow(family2, layout2)

    assert layout_saver._people_with_layout == people_with_layout
    assert layout_saver._people == people2


def test_write(
        layout_saver, family1, family2, layout2, error_message,
        people_with_layout, people_with_layout_error, people1, people2):
    layout_saver.write(family1, error_message)
    layout_saver.write(family2, layout2)

    assert layout_saver._people_with_layout ==\
        {**people_with_layout, **people_with_layout_error}
    assert layout_saver._people == {**people1, **people2}


def test_save(
        layout_saver, family1, family2, layout2, error_message,
        columns_labels, input_filename, output_filename, output, dict_reader,
        test_output):

    layout_saver.write(family1, error_message)
    layout_saver.write(family2, layout2)

    with patch(pedigrees.layout_saver.__name__ + '.open') as o:
        o.side_effect = lambda name, *args: open(name, *args)\
            if name != output_filename else name
        with patch('csv.DictWriter') as dw:
            dw.side_effect = lambda *args, **kwargs: dict_reader

            layout_saver.save(columns_labels)

    assert output.getvalue() == test_output
