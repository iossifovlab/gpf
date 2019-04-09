def test_effect_with_filter_missense(effect_with_filter_missense):
    assert effect_with_filter_missense.number_of_observed_events == 2
    assert effect_with_filter_missense.number_of_children_with_event == 1
    assert effect_with_filter_missense.observed_rate_per_child == 2 / 12
    assert effect_with_filter_missense.percent_of_children_with_events == \
        1 / 12
    assert effect_with_filter_missense.column == 'sib and phenotype2'

    assert effect_with_filter_missense.is_empty() is False

    assert len(effect_with_filter_missense.to_dict()) == 5


def test_effect_with_filter_frame_shift(effect_with_filter_frame_shift):
    assert effect_with_filter_frame_shift.number_of_observed_events == 2
    assert effect_with_filter_frame_shift.number_of_children_with_event == 2
    assert effect_with_filter_frame_shift.observed_rate_per_child == 2 / 12
    assert effect_with_filter_frame_shift.percent_of_children_with_events == \
        2 / 12
    assert effect_with_filter_frame_shift.column == 'prb and phenotype1'

    assert effect_with_filter_frame_shift.is_empty() is False

    assert len(effect_with_filter_frame_shift.to_dict()) == 5


def test_effect_with_filter_empty(effect_with_filter_empty):
    assert effect_with_filter_empty.number_of_observed_events == 0
    assert effect_with_filter_empty.number_of_children_with_event == 0
    assert effect_with_filter_empty.observed_rate_per_child == 0
    assert effect_with_filter_empty.percent_of_children_with_events == 0
    assert effect_with_filter_empty.column == 'dad and unknown'

    assert effect_with_filter_empty.is_empty() is True

    assert len(effect_with_filter_empty.to_dict()) == 5


def test_effect(effect):
    assert effect.effect_type == 'Missense'
    assert len(effect.row) == 16

    assert effect.is_row_empty() is False
    empty = effect.get_empty()
    empty_indexes = [i for i in range(len(empty)) if empty[i]]
    assert len(empty) == 16
    assert len(empty_indexes) == 14
    effect.remove_elements(empty_indexes)

    assert len(effect.row) == 2

    effect.remove_elements([0, 1])
    assert effect.is_row_empty() is True

    assert len(effect.to_dict()) == 2


def test_denovo_report_table(denovo_report_table):
    assert denovo_report_table.group_name == 'Role and Diagnosis'
    assert sorted(denovo_report_table.columns) == \
        sorted(['sib and phenotype2', 'prb and phenotype1'])
    assert denovo_report_table.effect_groups == ['Missense']
    assert denovo_report_table.effect_types == ['Frame-shift']
    assert len(denovo_report_table.rows) == 2

    assert denovo_report_table.is_empty() is False

    assert len(denovo_report_table.to_dict()) == 5


def test_denovo_report(denovo_report, denovo_variants_ds1):
    assert len(denovo_report.denovo_variants) == 8
    assert denovo_report.denovo_variants == denovo_variants_ds1
    assert len(denovo_report.tables) == 1

    assert denovo_report.is_empty() is False

    assert len(denovo_report.to_dict()) == 1
