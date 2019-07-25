from common_reports.denovo_report import EffectCell, EffectRow, \
    DenovoReportTable, DenovoReport


def test_effect_cell_missense(dataset1, denovo_variants_ds1, filter_objects):
    filter_object = filter_objects[0].get_filter_object_by_column_name(
        'sib and phenotype2')
    assert filter_object

    effect_cell = EffectCell(
        dataset1, denovo_variants_ds1, filter_object, 'Missense'
    )

    assert effect_cell.number_of_observed_events == 2
    assert effect_cell.number_of_children_with_event == 1
    assert effect_cell.observed_rate_per_child == 2.0 / 12.0
    assert effect_cell.percent_of_children_with_events == 1.0 / 12.0
    assert effect_cell.column == 'sib and phenotype2'

    assert effect_cell.is_empty() is False

    assert len(effect_cell.to_dict()) == 5


def test_effect_cell_frame_shift(
        dataset1, denovo_variants_ds1, filter_objects):
    filter_object = filter_objects[0].get_filter_object_by_column_name(
        'prb and phenotype1')
    assert filter_object

    effect_cell = EffectCell(
        dataset1, denovo_variants_ds1, filter_object, 'Frame-shift'
    )

    assert effect_cell.number_of_observed_events == 2
    assert effect_cell.number_of_children_with_event == 2
    assert effect_cell.observed_rate_per_child == 2.0 / 12.0
    assert effect_cell.percent_of_children_with_events == 2.0 / 12.0
    assert effect_cell.column == 'prb and phenotype1'

    assert effect_cell.is_empty() is False

    assert len(effect_cell.to_dict()) == 5


def test_effect_cell_empty(dataset1, denovo_variants_ds1, filter_objects):
    filter_object = filter_objects[0].get_filter_object_by_column_name(
        'dad and unknown')
    assert filter_object

    effect_cell = EffectCell(
        dataset1, denovo_variants_ds1, filter_object, 'Frame-shift'
    )

    assert effect_cell.number_of_observed_events == 0
    assert effect_cell.number_of_children_with_event == 0
    assert effect_cell.observed_rate_per_child == 0
    assert effect_cell.percent_of_children_with_events == 0
    assert effect_cell.column == 'dad and unknown'

    assert effect_cell.is_empty() is True

    assert len(effect_cell.to_dict()) == 5


def test_effect_row(dataset1, denovo_variants_ds1, filter_objects):
    effect_row = EffectRow(
        dataset1, denovo_variants_ds1, 'Missense', filter_objects[0]
    )

    assert effect_row.effect_type == 'Missense'
    assert len(effect_row.row) == 16

    assert effect_row.is_row_empty() is False
    empty = effect_row.get_empty()
    empty_indexes = [i for i in range(len(empty)) if empty[i]]
    assert len(empty) == 16
    assert len(empty_indexes) == 14
    effect_row.remove_elements(empty_indexes)

    assert len(effect_row.row) == 2

    effect_row.remove_elements([0, 1])
    assert effect_row.is_row_empty() is True

    assert len(effect_row.to_dict()) == 2


def test_denovo_report_table(dataset1, denovo_variants_ds1, filter_objects):
    denovo_report_table = DenovoReportTable(
        dataset1, denovo_variants_ds1, ['Missense', 'Splice-site'],
        ['Frame-shift', 'Nonsense'], filter_objects[0]
    )

    assert denovo_report_table.group_name == 'Role and Diagnosis'
    assert sorted(denovo_report_table.columns) == \
        sorted(['sib and phenotype2', 'prb and phenotype1'])
    assert denovo_report_table.effect_groups == ['Missense']
    assert denovo_report_table.effect_types == ['Frame-shift']
    assert len(denovo_report_table.rows) == 2

    assert denovo_report_table.is_empty() is False

    assert len(denovo_report_table.to_dict()) == 5


def test_denovo_report(dataset1, filter_objects, denovo_variants_ds1):
    denovo_report = DenovoReport(
        dataset1, ['Missense'], ['Frame-shift'], filter_objects
    )

    assert len(denovo_report.denovo_variants) == 8
    assert denovo_report.denovo_variants == denovo_variants_ds1
    assert len(denovo_report.tables) == 1

    assert denovo_report.is_empty() is False

    assert len(denovo_report.to_dict()) == 1


def test_denovo_report_empty(study2, filter_objects):
    denovo_report = DenovoReport(
        study2, ['Missense'], ['Frame-shift'], filter_objects
    )

    assert len(denovo_report.denovo_variants) == 0
    assert denovo_report.denovo_variants == []
    assert len(denovo_report.tables) == 0

    assert denovo_report.is_empty() is True

    assert len(denovo_report.to_dict()) == 1
