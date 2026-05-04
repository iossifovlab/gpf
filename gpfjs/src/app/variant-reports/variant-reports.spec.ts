/* eslint-disable @typescript-eslint/naming-convention */
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import {
  ChildrenCounter,
  DeNovoData,
  DenovoReport,
  EffectTypeRow,
  EffectTypeTable,
  FamilyCounter,
  FamilyReport,
  GroupCounter,
  Legend,
  LegendItem,
  PedigreeCounter,
  PeopleCounter,
  PeopleReport,
  VariantReport,
} from './variant-reports';

describe('ChildrenCounter', () => {
  it('should create children counter from json', () => {
    const childrenCounter = ChildrenCounter.fromJson(
      {
        column: 'fakeColumn',
        row1: 7,
      },
      'row1'
    );

    expect(childrenCounter).toStrictEqual(
      new ChildrenCounter('row1', 'fakeColumn', 7)
    );
  });
});

describe('GroupCounter', () => {
  it('should create group counter from json', () => {
    const groupCounter = GroupCounter.fromJson(
      {
        column: 'fakeColumn',
        row1: 7,
        row2: 13,
        row3: 17,
      },
      ['row1', 'row2', 'row3']
    );

    expect(groupCounter.column).toBe('fakeColumn');

    expect(groupCounter.childrenCounters).toStrictEqual([
      new ChildrenCounter('row1', 'fakeColumn', 7),
      new ChildrenCounter('row2', 'fakeColumn', 13),
      new ChildrenCounter('row3', 'fakeColumn', 17),
    ]);
  });
});

describe('PeopleCounter', () => {
  it('should create people counter from json', () => {
    const mockPeopleCounter = new PeopleCounter([
      new GroupCounter('col1', [
        new ChildrenCounter('row1', 'col1', 7),
        new ChildrenCounter('row2', 'col1', 13),
        new ChildrenCounter('row3', 'col1', 17),
      ]),
      new GroupCounter('col2', [
        new ChildrenCounter('row1', 'col2', 15),
        new ChildrenCounter('row2', 'col2', 666),
        new ChildrenCounter('row3', 'col2', 42),
      ]),
    ],
    'mock_group',
    ['row1', 'row2', 'row3'],
    ['col1', 'col2', 'col3']
    );

    const peopleCounter = PeopleCounter.fromJson({
      counters: [
        { column: 'col1', row1: 7, row2: 13, row3: 17 },
        { column: 'col2', row1: 15, row2: 666, row3: 42 },
      ],
      group_name: 'mock_group',
      rows: ['row1', 'row2', 'row3'],
      columns: ['col1', 'col2', 'col3'],
    });

    expect(peopleCounter).toStrictEqual(mockPeopleCounter);
  });

  it('should create children counter', () => {
    const mockPeopleCounter = new PeopleCounter([
      new GroupCounter('col1', [
        new ChildrenCounter('row1', 'col1', 7),
        new ChildrenCounter('row2', 'col1', 13),
        new ChildrenCounter('row3', 'col1', 17),
      ]),
      new GroupCounter('col2', [
        new ChildrenCounter('row1', 'col2', 15),
        new ChildrenCounter('row2', 'col2', 666),
        new ChildrenCounter('row3', 'col2', 42),
      ]),
    ],
    'mock_group',
    ['row1', 'row2', 'row3'],
    ['col1', 'col2', 'col3']
    );
    expect(mockPeopleCounter.getChildrenCounter('col1', 'row1')).toStrictEqual(new ChildrenCounter('row1', 'col1', 7));
    expect(mockPeopleCounter.getChildrenCounter('col2', 'row2')).toStrictEqual(
      new ChildrenCounter('row2', 'col2', 666)
    );
  });
});

describe('PeopleReport', () => {
  it('should create people data', () => {
    const peopleReport = [
      {
        counters: [
          { column: 'col1', row1: 7, row2: 13, row3: 17 },
          { column: 'col2', row1: 15, row2: 666, row3: 42 },
        ],
        group_name: 'mock_group',
        rows: ['row1', 'row2', 'row3'],
        columns: ['col1', 'col2', 'col3'],
      }, {
        counters: [
          { column: 'col3', row1: 67, row2: 12, row3: 18 },
          { column: 'col4', row1: 14, row2: 554, row3: 67 },
        ],
        group_name: 'mock_group',
        rows: ['row1', 'row2', 'row3'],
        columns: ['col1', 'col2', 'col3'],
      }
    ];

    const peopleCounter: PeopleCounter[] = [
      new PeopleCounter([
        new GroupCounter('col1', [
          new ChildrenCounter('row1', 'col1', 7),
          new ChildrenCounter('row2', 'col1', 13),
          new ChildrenCounter('row3', 'col1', 17),
        ]),
        new GroupCounter('col2', [
          new ChildrenCounter('row1', 'col2', 15),
          new ChildrenCounter('row2', 'col2', 666),
          new ChildrenCounter('row3', 'col2', 42),
        ]),
      ],
      'mock_group',
      ['row1', 'row2', 'row3'],
      ['col1', 'col2', 'col3']
      ),
      new PeopleCounter([
        new GroupCounter('col3', [
          new ChildrenCounter('row1', 'col3', 67),
          new ChildrenCounter('row2', 'col3', 12),
          new ChildrenCounter('row3', 'col3', 18),
        ]),
        new GroupCounter('col4', [
          new ChildrenCounter('row1', 'col4', 14),
          new ChildrenCounter('row2', 'col4', 554),
          new ChildrenCounter('row3', 'col4', 67),
        ]),
      ],
      'mock_group',
      ['row1', 'row2', 'row3'],
      ['col1', 'col2', 'col3']
      )
    ];

    expect(peopleCounter).toStrictEqual(PeopleReport.fromJson(peopleReport).peopleCounters);
  });
});

describe('PedigreeCounter', () => {
  it('should create pedigree counter from json', () => {
    const pedigreeCounter = new PedigreeCounter(1, 'groupName', [
      new PedigreeData(
        'identifier',
        'id',
        'mother',
        'father',
        'gender',
        'role',
        'color',
        [5, 7],
        true,
        'label',
        'smallLabel')], 5, ['tag1', 'tag2']);

    const pedigreeCounter2 = PedigreeCounter.fromJson(
      {
        counter_id: 1,
        pedigree: [
          ['identifier', 'id', 'mother', 'father', 'gender', 'role', 'color', ':5,7', true, 'label', 'smallLabel']
        ],
        pedigrees_count: 5,
        tags: ['tag1', 'tag2']
      }, 'groupName'
    );

    expect(pedigreeCounter).toStrictEqual(pedigreeCounter2);
  });
});

describe('FamilyCounter', () => {
  it('should create family counter from json', () => {
    const mockFamilyCounter = FamilyCounter.fromJson({
      counters: [
        {
          counter_id: 1,
          group_name: 'groupName1',
          pedigree: [
            [
              'identifier1',
              'id1',
              'mother1',
              'father1',
              'gender1',
              'role1',
              'color1',
              ':2,1',
              true,
              'label1',
              'smallLabel1'
            ]
          ],
          pedigrees_count: 5,
          tags: ['tag1', 'tag2'],
        },
        {
          counter_id: 2,
          group_name: 'groupName1',
          pedigree: [
            [
              'identifier2',
              'id2',
              'mother2',
              'father2',
              'gender2',
              'role2',
              'color2',
              ':5,7',
              false,
              'label2',
              'smallLabel2'
            ]
          ],
          pedigrees_count: 7,
          tags: ['tag3', 'tag4']
        }
      ], group_name: 'groupName1', phenotypes: ['phenotype4', 'phenotype5'], legend: [
        {
          id: 'id6',
          name: 'name7',
          color: 'color8'
        }, {
          id: 'id9',
          name: 'name10',
          color: 'color11'
        }
      ]
    });

    const mockFamilyCounter2 = new FamilyCounter([
      new PedigreeCounter(1, 'groupName1', [
        new PedigreeData(
          'identifier1',
          'id1',
          'mother1',
          'father1',
          'gender1',
          'role1',
          'color1',
          [2, 1],
          true,
          'label1',
          'smallLabel1')], 5, ['tag1', 'tag2']),
      new PedigreeCounter(2, 'groupName1', [
        new PedigreeData(
          'identifier2',
          'id2',
          'mother2',
          'father2',
          'gender2',
          'role2',
          'color2',
          [5, 7],
          false,
          'label2',
          'smallLabel2')], 7, ['tag3', 'tag4']),
    ], 'groupName1', ['phenotype4', 'phenotype5'],
    new Legend([new LegendItem('id6', 'name7', 'color8'), new LegendItem('id9', 'name10', 'color11')]));
    expect(mockFamilyCounter).toStrictEqual(mockFamilyCounter2);
  });
});


describe('FamilyReport', () => {
  it('should create family report from json', () => {
    const mockFamilyReport1 = new FamilyReport([
      new FamilyCounter([
        new PedigreeCounter(1, 'groupName1', [
          new PedigreeData(
            'identifier1', 'id1', 'mother1', 'father1', 'gender1', 'role1',
            'color1', [2, 1], true, 'label1', 'smallLabel1')], 5, ['tag1', 'tag2']),
        new PedigreeCounter(2, 'groupName1', [
          new PedigreeData(
            'identifier2', 'id2', 'mother2', 'father2', 'gender2', 'role2',
            'color2', [5, 7], false, 'label2', 'smallLabel2')], 7, ['tag3', 'tag4']),
      ], 'groupName1', ['phenotype4', 'phenotype5'],
      new Legend([new LegendItem('id6', 'name7', 'color8'), new LegendItem('id9', 'name10', 'color11')])
      ),
      new FamilyCounter([
        new PedigreeCounter(3, 'groupName2', [
          new PedigreeData(
            'identifier3', 'id3', 'mother3', 'father3', 'gender3', 'role3',
            'color3', [6, 8], false, 'label3', 'smallLabel3')], 1, ['tag5', 'tag6']),
        new PedigreeCounter(4, 'groupName2', [
          new PedigreeData(
            'identifier4', 'id4', 'mother4', 'father4', 'gender4', 'role4',
            'color4', [1, 1], true, 'label4', 'smallLabel4')], 10, ['tag7', 'tag8'])
      ], 'groupName2', ['phenotype6', 'phenotype7'],
      new Legend([new LegendItem('id12', 'name13', 'color14'), new LegendItem('id15', 'name16', 'color17')])
      ),
      new FamilyCounter([
        new PedigreeCounter(5, 'groupName3', [
          new PedigreeData(
            'identifier5', 'id5', 'mother5', 'father5',
            'gender5', 'role5', 'color5', [2, 2], true, 'label5', 'smallLabel5')], 9, ['tag9', 'tag10']),
        new PedigreeCounter(6, 'groupName3', [
          new PedigreeData(
            'identifier6', 'id6', 'mother6', 'father6',
            'gender6', 'role6', 'color6', [51, 7], false, 'label6', 'smallLabel6')], 85, ['tag11', 'tag12'])
      ], 'groupName3', ['phenotype8', 'phenotype9'],
      new Legend([new LegendItem('id18', 'name19', 'color20'), new LegendItem('id21', 'name22', 'color23')])
      ),
      new FamilyCounter([
        new PedigreeCounter(7, 'groupName4', [
          new PedigreeData(
            'identifier7', 'id7', 'mother7', 'father7',
            'gender7', 'role7', 'color7', [3, 3], false, 'label7', 'smallLabel7')], 14, ['tag13', 'tag14']),
        new PedigreeCounter(8, 'groupName4', [
          new PedigreeData(
            'identifier8', 'id8', 'mother8', 'father8',
            'gender8', 'role8', 'color8', [16, 13], true, 'label8', 'smallLabel8')], 11, ['tag15', 'tag16'])
      ], 'groupName4', ['phenotype10', 'phenotype11'],
      new Legend([new LegendItem('id24', 'name25', 'color26'), new LegendItem('id27', 'name28', 'color29')])
      ),
    ], 5);


    const mockFamilyReport2 = FamilyReport.fromJson([
      {
        counters: [
          {
            counter_id: 1,
            group_name: 'groupName1',
            pedigree: [
              [
                'identifier1',
                'id1',
                'mother1',
                'father1',
                'gender1',
                'role1',
                'color1',
                ':2,1',
                true,
                'label1',
                'smallLabel1'
              ]
            ],
            pedigrees_count: 5,
            tags: ['tag1', 'tag2']
          },
          {
            counter_id: 2,
            group_name: 'groupName1',
            pedigree: [
              [
                'identifier2',
                'id2',
                'mother2',
                'father2',
                'gender2',
                'role2',
                'color2',
                ':5,7',
                false,
                'label2',
                'smallLabel2'
              ]
            ],
            pedigrees_count: 7,
            tags: ['tag3', 'tag4']
          }
        ], group_name: 'groupName1', phenotypes: ['phenotype4', 'phenotype5'], legend: [
          {
            id: 'id6',
            name: 'name7',
            color: 'color8'
          }, {
            id: 'id9',
            name: 'name10',
            color: 'color11'
          }
        ]
      },
      {
        counters: [
          {
            counter_id: 3,
            group_name: 'groupName2',
            pedigree: [
              [
                'identifier3',
                'id3',
                'mother3',
                'father3',
                'gender3',
                'role3',
                'color3',
                ':6,8',
                false,
                'label3',
                'smallLabel3'
              ]
            ],
            pedigrees_count: 1,
            tags: ['tag5', 'tag6']
          },
          {
            counter_id: 4,
            group_name: 'groupName2',
            pedigree: [
              [
                'identifier4',
                'id4',
                'mother4',
                'father4',
                'gender4',
                'role4',
                'color4',
                ':1,1',
                true,
                'label4',
                'smallLabel4'
              ]
            ],
            pedigrees_count: 10,
            tags: ['tag7', 'tag8']
          }
        ], group_name: 'groupName2', phenotypes: ['phenotype6', 'phenotype7'], legend: [
          {
            id: 'id12',
            name: 'name13',
            color: 'color14'
          }, {
            id: 'id15',
            name: 'name16',
            color: 'color17'
          }
        ]
      },
      {
        counters: [
          {
            counter_id: 5,
            group_name: 'groupName5',
            pedigree: [
              [
                'identifier5',
                'id5',
                'mother5',
                'father5',
                'gender5',
                'role5',
                'color5',
                ':2,2',
                true,
                'label5',
                'smallLabel5'
              ]
            ],
            pedigrees_count: 9,
            tags: ['tag9', 'tag10']
          },
          {
            counter_id: 6,
            group_name: 'groupName6',
            pedigree: [
              [
                'identifier6',
                'id6',
                'mother6',
                'father6',
                'gender6',
                'role6',
                'color6',
                ':51,7',
                false,
                'label6',
                'smallLabel6'
              ]
            ],
            pedigrees_count: 85,
            tags: ['tag11', 'tag12']
          }
        ], group_name: 'groupName3', phenotypes: ['phenotype8', 'phenotype9'], legend: [
          {
            id: 'id18',
            name: 'name19',
            color: 'color20'
          }, {
            id: 'id21',
            name: 'name22',
            color: 'color23'
          }
        ]
      },
      {
        counters: [
          {
            counter_id: 7,
            group_name: 'groupName7',
            pedigree: [
              [
                'identifier7',
                'id7',
                'mother7',
                'father7',
                'gender7',
                'role7',
                'color7',
                ':3,3',
                false,
                'label7',
                'smallLabel7'
              ]
            ],
            pedigrees_count: 14,
            tags: ['tag13', 'tag14']
          },
          {
            counter_id: 8,
            group_name: 'groupName6',
            pedigree: [
              [
                'identifier8',
                'id8',
                'mother8',
                'father8',
                'gender8',
                'role8',
                'color8',
                ':16,13',
                true,
                'label8',
                'smallLabel8'
              ]
            ],
            pedigrees_count: 11,
            tags: ['tag15', 'tag16']
          }
        ], group_name: 'groupName4', phenotypes: ['phenotype10', 'phenotype11'], legend: [
          {
            id: 'id24',
            name: 'name25',
            color: 'color26'
          }, {
            id: 'id27',
            name: 'name28',
            color: 'color29'
          }
        ]
      }
    ], 5);

    expect(mockFamilyReport1).toStrictEqual(mockFamilyReport2);
  });
});

describe('DeNovoData', () => {
  it('should create de novo data from json', () => {
    const denovo1 = new DeNovoData('1', 2, 3, 4, 5);
    const denovo2 = DeNovoData.fromJson(
      {
        column: '1',
        number_of_observed_events: 2,
        number_of_children_with_event: 3,
        observed_rate_per_child: 4,
        percent_of_children_with_events: 5
      }
    );

    expect(denovo1).toStrictEqual(denovo2);
  });
});

describe('EffectTypeRow', () => {
  it('should create effects type row from json', () => {
    const mockEffectTypeRow1 = new EffectTypeRow(
      'effectType1',
      [
        new DeNovoData('1', 2, 3, 4, 5),
        new DeNovoData('2', 6, 7, 8, 9)
      ]
    );

    const mockEffectTypeRow2 = EffectTypeRow.fromJson({
      effect_type: 'effectType1',
      row: [
        {
          column: '1',
          number_of_observed_events: 2,
          number_of_children_with_event: 3,
          observed_rate_per_child: 4,
          percent_of_children_with_events: 5
        },
        {
          column: '2',
          number_of_observed_events: 6,
          number_of_children_with_event: 7,
          observed_rate_per_child: 8,
          percent_of_children_with_events: 9
        }
      ]
    }
    );

    expect(mockEffectTypeRow1).toStrictEqual(mockEffectTypeRow2);
  });
});

describe('EffectTypeTable', () => {
  it('should create effect type table from json', () => {
    const mockEffectTypeTable1 = new EffectTypeTable(
      [
        new EffectTypeRow('effectType1', [new DeNovoData('1', 2, 3, 4, 5), new DeNovoData('2', 6, 7, 8, 9)]),
        new EffectTypeRow('effectType2', [new DeNovoData('6', 7, 8, 9, 10), new DeNovoData('1', 2, 3, 4, 5)])
      ], 'groupName1', ['col1', 'col2'], ['effectGroup1', 'effectGroup2'], ['effectType1', 'effectType2']
    );

    const mockEffectTypeTable2 = EffectTypeTable.fromJson({
      rows: [
        {
          effect_type: 'effectType1',
          row: [
            {
              column: '1',
              number_of_observed_events: 2,
              number_of_children_with_event: 3,
              observed_rate_per_child: 4,
              percent_of_children_with_events: 5
            },
            {
              column: '2',
              number_of_observed_events: 6,
              number_of_children_with_event: 7,
              observed_rate_per_child: 8,
              percent_of_children_with_events: 9
            }
          ]},
        {
          effect_type: 'effectType2',
          row: [
            {
              column: '6',
              number_of_observed_events: 7,
              number_of_children_with_event: 8,
              observed_rate_per_child: 9,
              percent_of_children_with_events: 10
            },
            {
              column: '1',
              number_of_observed_events: 2,
              number_of_children_with_event: 3,
              observed_rate_per_child: 4,
              percent_of_children_with_events: 5
            }
          ]},
      ],
      group_name: 'groupName1',
      columns: ['col1', 'col2'],
      effect_groups: ['effectGroup1', 'effectGroup2'],
      effect_types: ['effectType1', 'effectType2']
    });

    expect(mockEffectTypeTable1).toStrictEqual(mockEffectTypeTable2);
  });
});

describe('DenovoReport', () => {
  it('should create json from denovo report', () => {
    const mockDenovoReport1 = new DenovoReport(
      [
        new EffectTypeTable(
          [
            new EffectTypeRow('effectType1', [new DeNovoData('1', 2, 3, 4, 5), new DeNovoData('2', 6, 7, 8, 9)]),
            new EffectTypeRow('effectType2', [new DeNovoData('6', 7, 8, 9, 10), new DeNovoData('1', 2, 3, 4, 5)])
          ], 'groupName1', ['col1', 'col2'], ['effectGroup1', 'effectGroup2'], ['effectType1', 'effectType2']),
        new EffectTypeTable(
          [
            new EffectTypeRow('effectType3', [new DeNovoData('5', 5, 6, 2, 1), new DeNovoData('2', 5, 4, 6, 4)]),
            new EffectTypeRow('effectType4', [new DeNovoData('7', 4, 5, 6, 1), new DeNovoData('7', 2, 1, 8, 3)])
          ], 'groupName2', ['col3', 'col4'], ['effectGroup2', 'effectGroup3'], ['effectType2', 'effectType3'])
      ]
    );

    const mockDenovoReport2 = DenovoReport.fromJson({
      tables: [
        {
          rows: [
            {
              effect_type: 'effectType1',
              row: [
                {
                  column: '1',
                  number_of_observed_events: 2,
                  number_of_children_with_event: 3,
                  observed_rate_per_child: 4,
                  percent_of_children_with_events: 5
                },
                {
                  column: '2',
                  number_of_observed_events: 6,
                  number_of_children_with_event: 7,
                  observed_rate_per_child: 8,
                  percent_of_children_with_events: 9
                }
              ]},
            {
              effect_type: 'effectType2',
              row: [
                {
                  column: '6',
                  number_of_observed_events: 7,
                  number_of_children_with_event: 8,
                  observed_rate_per_child: 9,
                  percent_of_children_with_events: 10
                },
                {
                  column: '1',
                  number_of_observed_events: 2,
                  number_of_children_with_event: 3,
                  observed_rate_per_child: 4,
                  percent_of_children_with_events: 5
                }
              ]},
          ],
          group_name: 'groupName1',
          columns: ['col1', 'col2'],
          effect_groups: ['effectGroup1', 'effectGroup2'],
          effect_types: ['effectType1', 'effectType2']
        },
        {
          rows: [
            {
              effect_type: 'effectType3',
              row: [
                {
                  column: '5',
                  number_of_observed_events: 5,
                  number_of_children_with_event: 6,
                  observed_rate_per_child: 2,
                  percent_of_children_with_events: 1
                },
                {
                  column: '2',
                  number_of_observed_events: 5,
                  number_of_children_with_event: 4,
                  observed_rate_per_child: 6,
                  percent_of_children_with_events: 4
                }
              ]},
            {
              effect_type: 'effectType4',
              row: [
                {
                  column: '7',
                  number_of_observed_events: 4,
                  number_of_children_with_event: 5,
                  observed_rate_per_child: 6,
                  percent_of_children_with_events: 1
                },
                {
                  column: '7',
                  number_of_observed_events: 2,
                  number_of_children_with_event: 1,
                  observed_rate_per_child: 8,
                  percent_of_children_with_events: 3
                }
              ]},
          ],
          group_name: 'groupName2',
          columns: ['col3', 'col4'],
          effect_groups: ['effectGroup2', 'effectGroup3'],
          effect_types: ['effectType2', 'effectType3']
        }
      ]
    });

    expect(mockDenovoReport1).toStrictEqual(mockDenovoReport2);
  });
});

describe('VariantReport', () => {
  it('should create variant report from json', () => {
    const mockVariantReport1 = new VariantReport('id1', 'studyName1', 'studyDescription1',
      new PeopleReport(
        [
          new PeopleCounter([
            new GroupCounter('col1', [
              new ChildrenCounter('row1', 'col1', 7),
              new ChildrenCounter('row2', 'col1', 13),
              new ChildrenCounter('row3', 'col1', 17),
            ]),
            new GroupCounter('col2', [
              new ChildrenCounter('row1', 'col2', 15),
              new ChildrenCounter('row2', 'col2', 666),
              new ChildrenCounter('row3', 'col2', 42),
            ]),
          ],
          'mock_group',
          ['row1', 'row2', 'row3'],
          ['col1', 'col2', 'col3']
          ),
          new PeopleCounter([
            new GroupCounter('col3', [
              new ChildrenCounter('row1', 'col3', 67),
              new ChildrenCounter('row2', 'col3', 12),
              new ChildrenCounter('row3', 'col3', 18),
            ]),
            new GroupCounter('col4', [
              new ChildrenCounter('row1', 'col4', 14),
              new ChildrenCounter('row2', 'col4', 554),
              new ChildrenCounter('row3', 'col4', 67),
            ]),
          ],
          'mock_group',
          ['row1', 'row2', 'row3'],
          ['col1', 'col2', 'col3']
          )
        ]),
      new FamilyReport([
        new FamilyCounter([
          new PedigreeCounter(1, 'groupName1', [
            new PedigreeData(
              'identifier1', 'id1', 'mother1', 'father1', 'gender1', 'role1',
              'color1', [2, 1], true, 'label1', 'smallLabel1')], 5, ['tag1', 'tag2']),
          new PedigreeCounter(2, 'groupName1', [
            new PedigreeData(
              'identifier2', 'id2', 'mother2', 'father2', 'gender2', 'role2',
              'color2', [5, 7], false, 'label2', 'smallLabel2')], 7, ['tag3', 'tag4'])
        ], 'groupName1', ['phenotype4', 'phenotype5'],
        new Legend([new LegendItem('id6', 'name7', 'color8'), new LegendItem('id9', 'name10', 'color11')])
        ),
        new FamilyCounter([
          new PedigreeCounter(3, 'groupName2', [
            new PedigreeData(
              'identifier3', 'id3', 'mother3', 'father3', 'gender3', 'role3',
              'color3', [6, 8], false, 'label3', 'smallLabel3')], 1, ['tag5', 'tag6']),
          new PedigreeCounter(4, 'groupName2', [
            new PedigreeData(
              'identifier4', 'id4', 'mother4', 'father4', 'gender4', 'role4',
              'color4', [1, 1], true, 'label4', 'smallLabel4')], 10, ['tag7', 'tag8'])
        ], 'groupName2', ['phenotype6', 'phenotype7'],
        new Legend([new LegendItem('id12', 'name13', 'color14'), new LegendItem('id15', 'name16', 'color17')])
        ),
        new FamilyCounter([
          new PedigreeCounter(5, 'groupName3', [
            new PedigreeData(
              'identifier5', 'id5', 'mother5', 'father5',
              'gender5', 'role5', 'color5', [2, 2], true, 'label5', 'smallLabel5')], 9, ['tag9', 'tag10']),
          new PedigreeCounter(6, 'groupName3', [
            new PedigreeData(
              'identifier6', 'id6', 'mother6', 'father6',
              'gender6', 'role6', 'color6', [51, 7], false, 'label6', 'smallLabel6')], 85, ['tag11', 'tag12'])
        ], 'groupName3', ['phenotype8', 'phenotype9'],
        new Legend([new LegendItem('id18', 'name19', 'color20'), new LegendItem('id21', 'name22', 'color23')])
        ),
        new FamilyCounter([
          new PedigreeCounter(7, 'groupName4', [
            new PedigreeData(
              'identifier7', 'id7', 'mother7', 'father7',
              'gender7', 'role7', 'color7', [3, 3], false, 'label7', 'smallLabel7')], 14, ['tag13', 'tag14']),
          new PedigreeCounter(8, 'groupName4', [
            new PedigreeData(
              'identifier8', 'id8', 'mother8', 'father8',
              'gender8', 'role8', 'color8', [16, 13], true, 'label8', 'smallLabel8')], 11, ['tag15', 'tag16'])
        ], 'groupName4', ['phenotype10', 'phenotype11'],
        new Legend([new LegendItem('id24', 'name25', 'color26'), new LegendItem('id27', 'name28', 'color29')])
        ),
      ], 5),
      new DenovoReport(
        [
          new EffectTypeTable(
            [
              new EffectTypeRow('effectType1', [new DeNovoData('1', 2, 3, 4, 5), new DeNovoData('2', 6, 7, 8, 9)]),
              new EffectTypeRow('effectType2', [new DeNovoData('6', 7, 8, 9, 10), new DeNovoData('1', 2, 3, 4, 5)])
            ], 'groupName1', ['col1', 'col2'], ['effectGroup1', 'effectGroup2'], ['effectType1', 'effectType2']),
          new EffectTypeTable(
            [
              new EffectTypeRow('effectType3', [new DeNovoData('5', 5, 6, 2, 1), new DeNovoData('2', 5, 4, 6, 4)]),
              new EffectTypeRow('effectType4', [new DeNovoData('7', 4, 5, 6, 1), new DeNovoData('7', 2, 1, 8, 3)])
            ], 'groupName2', ['col3', 'col4'], ['effectGroup2', 'effectGroup3'], ['effectType2', 'effectType3'])
        ]
      )
    );

    const mockVariantReport2 = VariantReport.fromJson(
      {
        id: 'id1',
        study_name: 'studyName1',
        study_description: 'studyDescription1',
        people_report: [{
          counters: [
            { column: 'col1', row1: 7, row2: 13, row3: 17 },
            { column: 'col2', row1: 15, row2: 666, row3: 42 },
          ],
          group_name: 'mock_group',
          rows: ['row1', 'row2', 'row3'],
          columns: ['col1', 'col2', 'col3'],
        }, {
          counters: [
            { column: 'col3', row1: 67, row2: 12, row3: 18 },
            { column: 'col4', row1: 14, row2: 554, row3: 67 },
          ],
          group_name: 'mock_group',
          rows: ['row1', 'row2', 'row3'],
          columns: ['col1', 'col2', 'col3'],
        }],
        families_report: [
          {
            counters: [
              {
                counter_id: 1,
                group_name: 'groupName1',
                pedigree: [
                  [
                    'identifier1',
                    'id1',
                    'mother1',
                    'father1',
                    'gender1',
                    'role1',
                    'color1',
                    ':2,1',
                    true,
                    'label1',
                    'smallLabel1'
                  ]
                ],
                pedigrees_count: 5,
                tags: ['tag1', 'tag2']
              },
              {
                counter_id: 2,
                group_name: 'groupName1',
                pedigree: [
                  [
                    'identifier2',
                    'id2',
                    'mother2',
                    'father2',
                    'gender2',
                    'role2',
                    'color2',
                    ':5,7',
                    false,
                    'label2',
                    'smallLabel2'
                  ]
                ],
                pedigrees_count: 7,
                tags: ['tag3', 'tag4']
              }
            ], group_name: 'groupName1', phenotypes: ['phenotype4', 'phenotype5'], legend: [
              {
                id: 'id6',
                name: 'name7',
                color: 'color8'
              }, {
                id: 'id9',
                name: 'name10',
                color: 'color11'
              }
            ]
          },
          {
            counters: [
              {
                counter_id: 3,
                group_name: 'groupName2',
                pedigree: [
                  [
                    'identifier3',
                    'id3',
                    'mother3',
                    'father3',
                    'gender3',
                    'role3',
                    'color3',
                    ':6,8',
                    false,
                    'label3',
                    'smallLabel3'
                  ]
                ],
                pedigrees_count: 1,
                tags: ['tag5', 'tag6']
              },
              {
                counter_id: 4,
                group_name: 'groupName2',
                pedigree: [
                  [
                    'identifier4',
                    'id4',
                    'mother4',
                    'father4',
                    'gender4',
                    'role4',
                    'color4',
                    ':1,1',
                    true,
                    'label4',
                    'smallLabel4'
                  ]
                ],
                pedigrees_count: 10,
                tags: ['tag7', 'tag8']
              }
            ], group_name: 'groupName2', phenotypes: ['phenotype6', 'phenotype7'], legend: [
              {
                id: 'id12',
                name: 'name13',
                color: 'color14'
              }, {
                id: 'id15',
                name: 'name16',
                color: 'color17'
              }
            ]
          },
          {
            counters: [
              {
                counter_id: 5,
                group_name: 'groupName5',
                pedigree: [
                  [
                    'identifier5',
                    'id5',
                    'mother5',
                    'father5',
                    'gender5',
                    'role5',
                    'color5',
                    ':2,2',
                    true,
                    'label5',
                    'smallLabel5'
                  ]
                ],
                pedigrees_count: 9,
                tags: ['tag9', 'tag10']
              },
              {
                counter_id: 6,
                group_name: 'groupName6',
                pedigree: [
                  [
                    'identifier6',
                    'id6',
                    'mother6',
                    'father6',
                    'gender6',
                    'role6',
                    'color6',
                    ':51,7',
                    false,
                    'label6',
                    'smallLabel6'
                  ]
                ],
                pedigrees_count: 85,
                tags: ['tag11', 'tag12']
              }
            ], group_name: 'groupName3', phenotypes: ['phenotype8', 'phenotype9'], legend: [
              {
                id: 'id18',
                name: 'name19',
                color: 'color20'
              }, {
                id: 'id21',
                name: 'name22',
                color: 'color23'
              }
            ]
          },
          {
            counters: [
              {
                counter_id: 7,
                group_name: 'groupName4',
                pedigree: [
                  [
                    'identifier7',
                    'id7',
                    'mother7',
                    'father7',
                    'gender7',
                    'role7',
                    'color7',
                    ':3,3',
                    false,
                    'label7',
                    'smallLabel7'
                  ]
                ],
                pedigrees_count: 14,
                tags: ['tag13', 'tag14']
              },
              {
                counter_id: 8,
                group_name: 'groupName4',
                pedigree: [
                  [
                    'identifier8',
                    'id8',
                    'mother8',
                    'father8',
                    'gender8',
                    'role8',
                    'color8',
                    ':16,13',
                    true,
                    'label8',
                    'smallLabel8'
                  ]
                ],
                pedigrees_count: 11,
                tags: ['tag15', 'tag16']
              }
            ], group_name: 'groupName4', phenotypes: ['phenotype10', 'phenotype11'], legend: [
              {
                id: 'id24',
                name: 'name25',
                color: 'color26'
              }, {
                id: 'id27',
                name: 'name28',
                color: 'color29'
              }
            ]
          }
        ], families: 5,
        denovo_report: {
          tables: [
            {
              rows: [
                {
                  effect_type: 'effectType1',
                  row: [
                    {
                      column: '1',
                      number_of_observed_events: 2,
                      number_of_children_with_event: 3,
                      observed_rate_per_child: 4,
                      percent_of_children_with_events: 5
                    },
                    {
                      column: '2',
                      number_of_observed_events: 6,
                      number_of_children_with_event: 7,
                      observed_rate_per_child: 8,
                      percent_of_children_with_events: 9
                    }
                  ]},
                {
                  effect_type: 'effectType2',
                  row: [
                    {
                      column: '6',
                      number_of_observed_events: 7,
                      number_of_children_with_event: 8,
                      observed_rate_per_child: 9,
                      percent_of_children_with_events: 10
                    },
                    {
                      column: '1',
                      number_of_observed_events: 2,
                      number_of_children_with_event: 3,
                      observed_rate_per_child: 4,
                      percent_of_children_with_events: 5
                    }
                  ]},
              ],
              group_name: 'groupName1',
              columns: ['col1', 'col2'],
              effect_groups: ['effectGroup1', 'effectGroup2'],
              effect_types: ['effectType1', 'effectType2']
            },
            {
              rows: [
                {
                  effect_type: 'effectType3',
                  row: [
                    {
                      column: '5',
                      number_of_observed_events: 5,
                      number_of_children_with_event: 6,
                      observed_rate_per_child: 2,
                      percent_of_children_with_events: 1
                    },
                    {
                      column: '2',
                      number_of_observed_events: 5,
                      number_of_children_with_event: 4,
                      observed_rate_per_child: 6,
                      percent_of_children_with_events: 4
                    }
                  ]},
                {
                  effect_type: 'effectType4',
                  row: [
                    {
                      column: '7',
                      number_of_observed_events: 4,
                      number_of_children_with_event: 5,
                      observed_rate_per_child: 6,
                      percent_of_children_with_events: 1
                    },
                    {
                      column: '7',
                      number_of_observed_events: 2,
                      number_of_children_with_event: 1,
                      observed_rate_per_child: 8,
                      percent_of_children_with_events: 3
                    }
                  ]},
              ],
              group_name: 'groupName2',
              columns: ['col3', 'col4'],
              effect_groups: ['effectGroup2', 'effectGroup3'],
              effect_types: ['effectType2', 'effectType3']
            }
          ]
        }
      });

    expect(mockVariantReport1).toStrictEqual(mockVariantReport2);
  });
});

describe('LegendItem', () => {
  it('should create legend item from json', () => {
    const mockLegendItem = LegendItem.fromJson(
      {
        id: 'id1',
        name: 'name1',
        color: 'color1'
      }
    );

    expect(mockLegendItem).toStrictEqual(new LegendItem('id1', 'name1', 'color1'));
  });
});

describe('Legend', () => {
  it('should create legend from json', () => {
    const mockLegend = Legend.fromList(
      [{
        id: 'id1',
        name: 'name1',
        color: 'color1'
      },
      {
        id: 'id2',
        name: 'name2',
        color: 'color2'
      }]
    );

    expect(mockLegend).toStrictEqual(
      new Legend([new LegendItem('id1', 'name1', 'color1'), new LegendItem('id2', 'name2', 'color2')])
    );
  });
});
