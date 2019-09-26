from dae.pedigrees.layout_saver import LayoutSaver
import dae.pedigrees.layout_saver


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

    expected_layout = people_with_layout.copy()
    expected_layout.update(people_with_layout_error)

    assert layout_saver._people_with_layout == expected_layout

    expected_people = people1.copy()
    expected_people.update(people2)

    assert layout_saver._people == expected_people


# FIXME: this test should probably be rewritten to use and captured stdout
#  instead of trying to mock `open`
def test_save(
        layout_saver, family1, family2, layout2, error_message,
        columns_labels, input_filename, output_filename, output, dict_writer,
        test_output, mocker):

    layout_saver.write(family1, error_message)
    layout_saver.write(family2, layout2)

    def new_open(name, *args, **kwargs):
        return open(name, *args, **kwargs) if name != output_filename else name

    with mocker.patch(
        dae.pedigrees.layout_saver.__name__ + '.open',
            side_effect=new_open):
        # o.
        with mocker.patch(
                'csv.DictWriter',
                side_effect=lambda *args, **kwargs: dict_writer):
            # dw.

            layout_saver.save(columns_labels)

    assert output.getvalue() == test_output
