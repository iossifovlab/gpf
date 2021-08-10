from box import Box


def test_drawing(drawing_from_family2, layout_from_family2):
    assert drawing_from_family2 is not None

    assert drawing_from_family2._x_offset == 0
    assert drawing_from_family2._y_offset == 0
    assert drawing_from_family2._gap == 4.0
    # assert len(drawing_from_family2._layout._intervals) == len(
    #     layout_from_family2._intervals
    # )
    assert drawing_from_family2.show_id is True
    assert drawing_from_family2.show_family is True
    assert drawing_from_family2.figsize == (7, 10)


def test_drawing_draw(drawing_from_family2):
    figure = drawing_from_family2.draw()

    assert figure.bbox_inches.x0 == 0
    assert figure.bbox_inches.y0 == 0
    assert figure.bbox_inches.x1 == 7
    assert figure.bbox_inches.y1 == 10

    assert len(figure._axstack.as_list()) == 2
    axes1 = figure._axstack.as_list()[0]
    axes2 = figure._axstack.as_list()[1]

    assert axes1.axison is False
    assert axes1.stale is True
    # assert axes1._aspect == 1.0
    assert axes1._adjustable == "datalim"
    assert axes1._anchor == "C"
    assert len(axes1.lines) == 3
    assert len(axes1.patches) == 4

    assert axes1.patches[0].center == [20.5, 50.5]
    assert axes1.patches[0].radius == 10.5
    assert axes1.patches[0]._facecolor == (1.0, 1.0, 1.0, 1.0)
    assert axes1.patches[0]._edgecolor == (0, 0, 0, 1.0)

    assert axes1.patches[1]._x0 == 53.5
    assert axes1.patches[1]._y0 == 40.0
    # assert axes1.patches[1]._x1 == 74.5
    # assert axes1.patches[1]._y1 == 61.0
    assert axes1.patches[1]._facecolor == (
        0.5019607843137255,
        0.5019607843137255,
        0.5019607843137255,
        1.0,
    )
    assert axes1.patches[1]._edgecolor == (0, 0, 0, 1.0)

    assert axes1.patches[2]._x0 == 31.75
    assert axes1.patches[2]._y0 == 10.0
    # assert axes1.patches[2]._x1 == 52.75
    # assert axes1.patches[2]._y1 == 31.0
    assert axes1.patches[2]._facecolor == (1.0, 0, 0, 1.0)
    assert axes1.patches[2]._edgecolor == (0, 0, 0, 1.0)

    assert axes1.patches[3]._facecolor == (0, 0, 0, 1.0)
    assert axes1.patches[3]._edgecolor == (0, 0, 0, 1.0)
    assert axes1.patches[3]._linewidth == 0.1

    assert axes2.axison is False
    assert axes2.stale is True
    # assert axes2._aspect == 1.0
    assert axes2._adjustable == "datalim"
    assert axes2._anchor == "C"

    assert axes2.table._loc == 9

    table_cells = axes2.table._cells
    assert len(table_cells) == 40

    assert table_cells[(0, 0)]._text._text == "familyId"
    assert table_cells[(0, 1)]._text._text == "individualId"
    assert table_cells[(0, 2)]._text._text == "father"
    assert table_cells[(0, 3)]._text._text == "mother"
    assert table_cells[(0, 4)]._text._text == "sex"
    assert table_cells[(0, 5)]._text._text == "status"
    assert table_cells[(0, 6)]._text._text == "role"
    assert table_cells[(0, 7)]._text._text == "layout"

    assert table_cells[(1, 1)]._text._text == "mom2"
    assert table_cells[(2, 1)]._text._text == "dad2"
    assert table_cells[(3, 1)]._text._text == "id2"


def test_draw_families_report(drawing_from_family2, layout_from_family2):
    families_report = drawing_from_family2.draw_families_report(
        Box(
            {
                "people_counters": [
                    Box(
                        {
                            "group_name": "Group 1",
                            "counters": [
                                Box(
                                    {
                                        "column": "Column 1",
                                        "people_male": 2,
                                        "people_female": 1,
                                        "people_unspecified": 0,
                                        "people_total": 3,
                                    }
                                )
                            ],
                        }
                    )
                ],
                "families_total": 1,
                "families_counters": [
                    Box(
                        {
                            "counters": [
                                Box(
                                    {
                                        "counters": [
                                            Box(
                                                {
                                                    "pedigree": [
                                                        [
                                                            "fam2",
                                                            "id2",
                                                            "dad2",
                                                            "mom2",
                                                            "M",
                                                            "prb",
                                                            "#E35252",
                                                            "2:100.0,75.0",
                                                            False,
                                                            "",
                                                            "",
                                                        ],
                                                        [
                                                            "fam2",
                                                            "mom2",
                                                            "0",
                                                            "0",
                                                            "F",
                                                            "mom",
                                                            "#FFFFFF",
                                                            "1:50.0,50.0",
                                                            False,
                                                            "",
                                                            "",
                                                        ],
                                                        [
                                                            "fam2",
                                                            "dad2",
                                                            "0",
                                                            "0",
                                                            "M",
                                                            "dad",
                                                            "#E0E0E0",
                                                            "1:50.0,100.0",
                                                            True,
                                                            "",
                                                            "",
                                                        ],
                                                    ],
                                                    "pedigrees_count": 1,
                                                }
                                            ),
                                            Box(
                                                {
                                                    "pedigree": [
                                                        [
                                                            "fam1",
                                                            "id1",
                                                            "dad1",
                                                            "mom1",
                                                            "M",
                                                            "prb",
                                                            "#E35252",
                                                            "2:100.0,75.0",
                                                            False,
                                                            "",
                                                            "",
                                                        ]
                                                    ],
                                                    "pedigrees_count": 1,
                                                }
                                            ),
                                        ]
                                    }
                                )
                            ]
                        }
                    )
                ],
            }
        ),
        dict({"fam1": None, "fam2": layout_from_family2, }),
    )

    assert len(families_report) == 2

    figure1 = families_report[0]
    figure2 = families_report[1]

    assert figure1.bbox_inches.x0 == 0
    assert figure1.bbox_inches.y0 == 0
    assert figure1.bbox_inches.x1 == 7
    assert figure1.bbox_inches.y1 == 10

    assert len(figure1._axstack.as_list()) == 1

    axes1 = figure1._axstack.as_list()[0]
    table_cells = axes1.table._cells

    assert len(table_cells) == 10

    assert table_cells[(0, 0)]._text._text == "Group 1"
    assert table_cells[(1, 0)]._text._text == "People Male"
    assert table_cells[(2, 0)]._text._text == "People Female"
    assert table_cells[(3, 0)]._text._text == "People Unspecified"
    assert table_cells[(4, 0)]._text._text == "People Total"
    assert table_cells[(0, 1)]._text._text == "Column 1"
    assert table_cells[(1, 1)]._text._text == "2"
    assert table_cells[(2, 1)]._text._text == "1"
    assert table_cells[(3, 1)]._text._text == "0"
    assert table_cells[(4, 1)]._text._text == "3"

    assert figure2.bbox_inches.x0 == 0
    assert figure2.bbox_inches.y0 == 0
    assert figure2.bbox_inches.x1 == 7
    assert figure2.bbox_inches.y1 == 10

    assert len(figure2._axstack.as_list()) == 9
    axes1 = figure2._axstack.as_list()[0]
    axes2 = figure2._axstack.as_list()[1]

    assert axes1.axison is False
    assert axes1.stale is True
    # assert axes1._aspect == 1.0
    assert axes1._adjustable == "datalim"
    assert axes1._anchor == "C"
    assert len(axes1.lines) == 3
    assert len(axes1.patches) == 4

    assert axes1.patches[0].center == [20.5, 50.5]
    assert axes1.patches[0].radius == 10.5
    assert axes1.patches[0]._facecolor == (1.0, 1.0, 1.0, 1.0)
    assert axes1.patches[0]._edgecolor == (0, 0, 0, 1.0)

    assert axes1.patches[1]._x0 == 53.5
    assert axes1.patches[1]._y0 == 40.0
    # assert axes1.patches[1]._x1 == 74.5
    # assert axes1.patches[1]._y1 == 61.0
    assert axes1.patches[1]._facecolor == (
        0.5019607843137255,
        0.5019607843137255,
        0.5019607843137255,
        1.0,
    )
    assert axes1.patches[1]._edgecolor == (0, 0, 0, 1.0)

    assert axes1.patches[2]._x0 == 31.75
    assert axes1.patches[2]._y0 == 10.0
    # assert axes1.patches[2]._x1 == 52.75
    # assert axes1.patches[2]._y1 == 31.0
    assert axes1.patches[2]._facecolor == (1.0, 0, 0, 1.0)
    assert axes1.patches[2]._edgecolor == (0, 0, 0, 1.0)

    assert axes1.patches[3]._facecolor == (0, 0, 0, 1.0)
    assert axes1.patches[3]._edgecolor == (0, 0, 0, 1.0)
    assert axes1.patches[3]._linewidth == 0.1

    assert axes2.axison is False
    assert axes2.stale is True
    # assert axes2._aspect == 1.0
    assert axes2._adjustable == "datalim"
    assert axes2._anchor == "C"
    assert len(axes2.texts) == 1
    assert axes2.texts[0]._text == "Invalid coordinates"
    assert axes2.texts[0]._x == 0.5
    assert axes2.texts[0]._y == 1.1

    assert len(figure2.texts) == 1
    assert figure2.texts[0]._text == "Families counters"
    assert figure2.texts[0]._x == 0.5
    assert figure2.texts[0]._y == 0.95
