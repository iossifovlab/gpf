import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import {
  ChildrenCounter,
  DeNovoData,
  DenovoReport,
  EffectTypeRow,
  EffectTypeTable,
  FamilyCounter,
  FamilyCounters,
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

    expect(childrenCounter).toEqual(
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

    expect(groupCounter.column).toEqual('fakeColumn');

    expect(groupCounter.childrenCounters as ChildrenCounter[]).toEqual([
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

    expect(peopleCounter).toEqual(mockPeopleCounter);
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
    expect(mockPeopleCounter.getChildrenCounter('col1', 'row1')).toEqual(new ChildrenCounter('row1', 'col1', 7));
    expect(mockPeopleCounter.getChildrenCounter('col2', 'row2')).toEqual(new ChildrenCounter('row2', 'col2', 666));
  });
});

describe('PeopleReport', () => {
  it('should create people data', () => {
      const peopleReport = {
        people_counters: [
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
        ]
      };

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

      expect(peopleCounter).toEqual(PeopleReport.fromJson(peopleReport).peopleCounters);
  });
});

describe('PedigreeCounter', () => {
  it('should create pedigree counter from json', () => {

    const pedigreeCounter = new PedigreeCounter([
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
        'smallLabel')], 5);

    const pedigreeCounter2 = PedigreeCounter.fromArray({
        pedigree: [
            ['identifier', 'id', 'mother', 'father', 'gender', 'role', 'color', ':5,7', true, 'label', 'smallLabel']
        ],
        pedigrees_count: 5
    });

    expect(pedigreeCounter as PedigreeCounter).toEqual(pedigreeCounter2 as PedigreeCounter);
  });
});

describe('FamilyCounter', () => {
  it('should create family counter from json', () => {
    const mockFamilyCounter = FamilyCounter.fromJson({
      counters: [
        {
          pedigree: [
            ['identifier1', 'id1', 'mother1', 'father1', 'gender1', 'role1', 'color1', ':2,1', true, 'label1', 'smallLabel1']
          ],
          pedigrees_count: 5
        },
        {
          pedigree: [
            ['identifier2', 'id2', 'mother2', 'father2', 'gender2', 'role2', 'color2', ':5,7', false, 'label2', 'smallLabel2']
          ],
          pedigrees_count: 7
        }
      ]
    });

    const mockFamilyCounter2 = new FamilyCounter([
      new PedigreeCounter([
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
          'smallLabel1')], 5),
      new PedigreeCounter([
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
          'smallLabel2')], 7)
    ]);

    expect(mockFamilyCounter as FamilyCounter).toEqual(mockFamilyCounter2 as FamilyCounter);
  });
});

describe('FamilyCounters', () => {
  it('should create family counters from json', () => {
    const mockFamilyCounters1 = new FamilyCounters([
        new FamilyCounter([
          new PedigreeCounter([
            new PedigreeData(
              'identifier1', 'id1', 'mother1', 'father1', 'gender1', 'role1', 'color1', [2, 1], true, 'label1', 'smallLabel1')], 5),
          new PedigreeCounter([
            new PedigreeData(
              'identifier2', 'id2', 'mother2', 'father2', 'gender2', 'role2', 'color2', [5, 7], false, 'label2', 'smallLabel2')], 7)
        ]),
        new FamilyCounter([
          new PedigreeCounter([
            new PedigreeData(
              'identifier3', 'id3', 'mother3', 'father3', 'gender3', 'role3', 'color3', [6, 8], false, 'label3', 'smallLabel3')], 1),
          new PedigreeCounter([
            new PedigreeData(
              'identifier4', 'id4', 'mother4', 'father4', 'gender4', 'role4', 'color4', [1, 1], true, 'label4', 'smallLabel4')], 10)
        ]),
      ],
      'groupName1', ['pheno1', 'pheno2'],
      new Legend(
        [
          new LegendItem('id1', 'name1', 'color1'),
          new LegendItem('id2', 'name2', 'color2')
        ]
    ));

    const mockFamilyCounters2 = FamilyCounters.fromJson({
      counters: [
        {
          counters: [
            {
              pedigree: [
                ['identifier1', 'id1', 'mother1', 'father1', 'gender1', 'role1', 'color1', ':2,1', true, 'label1', 'smallLabel1']
              ],
              pedigrees_count: 5
            },
            {
              pedigree: [
                ['identifier2', 'id2', 'mother2', 'father2', 'gender2', 'role2', 'color2', ':5,7', false, 'label2', 'smallLabel2']
              ],
              pedigrees_count: 7
            }
          ]
        }, {
          counters: [
            {
              pedigree: [
                ['identifier3', 'id3', 'mother3', 'father3', 'gender3', 'role3', 'color3', ':6,8', false, 'label3', 'smallLabel3']
              ],
              pedigrees_count: 1
            },
            {
              pedigree: [
                ['identifier4', 'id4', 'mother4', 'father4', 'gender4', 'role4', 'color4', ':1,1', true, 'label4', 'smallLabel4']
              ],
              pedigrees_count: 10
            }
          ]
        }
      ], group_name: 'groupName1', phenotypes: ['pheno1', 'pheno2'], legend: [
        {id: 'id1', name: 'name1', color: 'color1'},
        {id: 'id2', name: 'name2', color: 'color2'}
      ]
    });

    expect(mockFamilyCounters1).toEqual(mockFamilyCounters2);
  });
});

describe('FamilyReport', () => {
  it('should create family report from json', () => {
    const mockFamilyReport1 = new FamilyReport(
      [
        new FamilyCounters([
          new FamilyCounter([
            new PedigreeCounter([
              new PedigreeData(
                'identifier1', 'id1', 'mother1', 'father1', 'gender1', 'role1', 'color1', [2, 1], true, 'label1', 'smallLabel1')], 5),
            new PedigreeCounter([
              new PedigreeData(
                'identifier2', 'id2', 'mother2', 'father2', 'gender2', 'role2', 'color2', [5, 7], false, 'label2', 'smallLabel2')], 7)
          ]),
          new FamilyCounter([
            new PedigreeCounter([
              new PedigreeData(
                'identifier3', 'id3', 'mother3', 'father3', 'gender3', 'role3', 'color3', [6, 8], false, 'label3', 'smallLabel3')], 1),
            new PedigreeCounter([
              new PedigreeData(
                'identifier4', 'id4', 'mother4', 'father4', 'gender4', 'role4', 'color4', [1, 1], true, 'label4', 'smallLabel4')], 10)
          ]),
        ],
        'groupName1', ['pheno1', 'pheno2'],
        new Legend(
          [
            new LegendItem('id1', 'name1', 'color1'),
            new LegendItem('id2', 'name2', 'color2')
          ]
        )),
        new FamilyCounters([
          new FamilyCounter([
            new PedigreeCounter([
              new PedigreeData(
                'identifier5', 'id5', 'mother5', 'father5', 'gender5', 'role5', 'color5', [2, 2], true, 'label5', 'smallLabel5')], 9),
            new PedigreeCounter([
              new PedigreeData(
                'identifier6', 'id6', 'mother6', 'father6', 'gender6', 'role6', 'color6', [51, 7], false, 'label6', 'smallLabel6')], 85)
          ]),
          new FamilyCounter([
            new PedigreeCounter([
              new PedigreeData(
                'identifier7', 'id7', 'mother7', 'father7', 'gender7', 'role7', 'color7', [3, 3], false, 'label7', 'smallLabel7')], 14),
            new PedigreeCounter([
              new PedigreeData(
                'identifier8', 'id8', 'mother8', 'father8', 'gender8', 'role8', 'color8', [16, 13], true, 'label8', 'smallLabel8')], 11)
          ]),
        ],
        'groupName2', ['pheno3', 'pheno4'],
        new Legend(
          [
            new LegendItem('id3', 'name3', 'color3'),
            new LegendItem('id4', 'name4', 'color4')
          ]
        ))
      ], 5
    );

    const mockFamilyReport2 = FamilyReport.fromJson(
      {
        families_counters: [{
            counters: [
              {
                counters: [
                  {
                    pedigree: [
                      ['identifier1', 'id1', 'mother1', 'father1', 'gender1', 'role1', 'color1', ':2,1', true, 'label1', 'smallLabel1']
                    ],
                    pedigrees_count: 5
                  },
                  {
                    pedigree: [
                      [
                        'identifier2', 'id2', 'mother2', 'father2', 'gender2', 'role2', 'color2', ':5,7', false, 'label2', 'smallLabel2'
                      ]
                    ],
                    pedigrees_count: 7
                  }
                ]
              }, {
                counters: [
                  {
                    pedigree: [
                      [
                        'identifier3', 'id3', 'mother3', 'father3', 'gender3', 'role3', 'color3', ':6,8', false, 'label3', 'smallLabel3'
                      ]
                    ],
                    pedigrees_count: 1
                  },
                  {
                    pedigree: [
                      ['identifier4', 'id4', 'mother4', 'father4', 'gender4', 'role4', 'color4', ':1,1', true, 'label4', 'smallLabel4']
                    ],
                    pedigrees_count: 10
                  }
                ]
              }
            ], group_name: 'groupName1', phenotypes: ['pheno1', 'pheno2'], legend: [
              {id: 'id1', name: 'name1', color: 'color1'},
              {id: 'id2', name: 'name2', color: 'color2'}
            ]
        },
        {
            counters: [
              {
                counters: [
                  {
                    pedigree: [
                      ['identifier5', 'id5', 'mother5', 'father5', 'gender5', 'role5', 'color5', ':2,2', true, 'label5', 'smallLabel5']
                    ],
                    pedigrees_count: 9
                  },
                  {
                    pedigree: [
                      [
                        'identifier6', 'id6', 'mother6', 'father6', 'gender6', 'role6', 'color6', ':51,7', false, 'label6', 'smallLabel6'
                      ]
                    ],
                    pedigrees_count: 85
                  }
                ]
              }, {
                counters: [
                  {
                    pedigree: [
                      [
                        'identifier7', 'id7', 'mother7', 'father7', 'gender7', 'role7', 'color7', ':3,3', false, 'label7', 'smallLabel7'
                      ]
                    ],
                    pedigrees_count: 14
                  },
                  {
                    pedigree: [
                      ['identifier8', 'id8', 'mother8', 'father8', 'gender8', 'role8', 'color8', ':16,13', true, 'label8', 'smallLabel8']
                    ],
                    pedigrees_count: 11
                  }
                ]
              }
            ], group_name: 'groupName2', phenotypes: ['pheno3', 'pheno4'], legend: [
              {id: 'id3', name: 'name3', color: 'color3'},
              {id: 'id4', name: 'name4', color: 'color4'}
            ]
        }],
        families_total: 5
      }
    );

    expect(mockFamilyReport1).toEqual(mockFamilyReport2);
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

    expect(denovo1).toEqual(denovo2);
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
        row : [
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

    expect(mockEffectTypeRow1).toEqual(mockEffectTypeRow2);
  });
});

describe('EffectTypeTable', () => {
  it('should create effect type table from json', () => {
    const mockEffectTypeTable1 = new EffectTypeTable(
      [
        new EffectTypeRow('effectType1', [ new DeNovoData('1', 2, 3, 4, 5), new DeNovoData('2', 6, 7, 8, 9)]),
        new EffectTypeRow('effectType2', [ new DeNovoData('6', 7, 8, 9, 10), new DeNovoData('1', 2, 3, 4, 5)])
      ], 'groupName1', ['col1', 'col2'], ['effectGroup1', 'effectGroup2'], ['effectType1', 'effectType2']
    );

    const mockEffectTypeTable2 = EffectTypeTable.fromJson({
      rows: [
        {
        effect_type: 'effectType1',
        row : [
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
          row : [
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

    expect(mockEffectTypeTable1).toEqual(mockEffectTypeTable2);
  });
});

describe('DenovoReport', () => {
  it('should create json from denovo report', () => {
    const mockDenovoReport1 = new DenovoReport(
      [
      new EffectTypeTable(
        [
          new EffectTypeRow('effectType1', [ new DeNovoData('1', 2, 3, 4, 5), new DeNovoData('2', 6, 7, 8, 9)]),
          new EffectTypeRow('effectType2', [ new DeNovoData('6', 7, 8, 9, 10), new DeNovoData('1', 2, 3, 4, 5)])
        ], 'groupName1', ['col1', 'col2'], ['effectGroup1', 'effectGroup2'], ['effectType1', 'effectType2']),
        new EffectTypeTable(
          [
            new EffectTypeRow('effectType3', [ new DeNovoData('5', 5, 6, 2, 1), new DeNovoData('2', 5, 4, 6, 4)]),
            new EffectTypeRow('effectType4', [ new DeNovoData('7', 4, 5, 6, 1), new DeNovoData('7', 2, 1, 8, 3)])
          ], 'groupName2', ['col3', 'col4'], ['effectGroup2', 'effectGroup3'], ['effectType2', 'effectType3'])
      ]
    );

    const mockDenovoReport2 = DenovoReport.fromJson({
      tables: [
      {
        rows: [
          {
          effect_type: 'effectType1',
          row : [
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
            row : [
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
          row : [
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
            row : [
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

    expect(mockDenovoReport1).toEqual(mockDenovoReport2);
  });
});

describe('VariantReport', () => {
  it('should create variant report from json', () => {
    const mockVariantReport1 = new VariantReport('id1', 'studyName1', 'studyDescription1',
      new PeopleReport(
      PeopleCounter[2] = [
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
      new FamilyReport(
        [
          new FamilyCounters([
            new FamilyCounter([
              new PedigreeCounter([
                new PedigreeData(
                  'identifier1', 'id1', 'mother1', 'father1', 'gender1', 'role1', 'color1', [2, 1], true, 'label1', 'smallLabel1')], 5),
              new PedigreeCounter([
                new PedigreeData(
                  'identifier2', 'id2', 'mother2', 'father2', 'gender2', 'role2', 'color2', [5, 7], false, 'label2', 'smallLabel2')], 7)
            ]),
            new FamilyCounter([
              new PedigreeCounter([
                new PedigreeData(
                  'identifier3', 'id3', 'mother3', 'father3', 'gender3', 'role3', 'color3', [6, 8], false, 'label3', 'smallLabel3')], 1),
              new PedigreeCounter([
                new PedigreeData(
                  'identifier4', 'id4', 'mother4', 'father4', 'gender4', 'role4', 'color4', [1, 1], true, 'label4', 'smallLabel4')], 10)
            ]),
          ],
          'groupName1', ['pheno1', 'pheno2'],
          new Legend(
            [
              new LegendItem('id1', 'name1', 'color1'),
              new LegendItem('id2', 'name2', 'color2')
            ]
          )),
          new FamilyCounters([
            new FamilyCounter([
              new PedigreeCounter([
                new PedigreeData(
                  'identifier5', 'id5', 'mother5', 'father5', 'gender5', 'role5', 'color5', [2, 2], true, 'label5', 'smallLabel5')], 9),
              new PedigreeCounter([
                new PedigreeData(
                  'identifier6', 'id6', 'mother6', 'father6', 'gender6', 'role6', 'color6', [51, 7], false, 'label6', 'smallLabel6')], 85)
            ]),
            new FamilyCounter([
              new PedigreeCounter([
                new PedigreeData(
                  'identifier7', 'id7', 'mother7', 'father7', 'gender7', 'role7', 'color7', [3, 3], false, 'label7', 'smallLabel7')], 14),
              new PedigreeCounter([
                new PedigreeData(
                  'identifier8', 'id8', 'mother8', 'father8', 'gender8', 'role8', 'color8', [16, 13], true, 'label8', 'smallLabel8')], 11)
            ]),
          ],
          'groupName2', ['pheno3', 'pheno4'],
          new Legend(
            [
              new LegendItem('id3', 'name3', 'color3'),
              new LegendItem('id4', 'name4', 'color4')
            ]
          ))
        ], 5
      ),
      new DenovoReport(
        [
        new EffectTypeTable(
          [
            new EffectTypeRow('effectType1', [ new DeNovoData('1', 2, 3, 4, 5), new DeNovoData('2', 6, 7, 8, 9)]),
            new EffectTypeRow('effectType2', [ new DeNovoData('6', 7, 8, 9, 10), new DeNovoData('1', 2, 3, 4, 5)])
          ], 'groupName1', ['col1', 'col2'], ['effectGroup1', 'effectGroup2'], ['effectType1', 'effectType2']),
          new EffectTypeTable(
            [
              new EffectTypeRow('effectType3', [ new DeNovoData('5', 5, 6, 2, 1), new DeNovoData('2', 5, 4, 6, 4)]),
              new EffectTypeRow('effectType4', [ new DeNovoData('7', 4, 5, 6, 1), new DeNovoData('7', 2, 1, 8, 3)])
            ], 'groupName2', ['col3', 'col4'], ['effectGroup2', 'effectGroup3'], ['effectType2', 'effectType3'])
        ]
      )
    );

    const mockVariantReport2 = VariantReport.fromJson(
      {
        id: 'id1',
        study_name: 'studyName1',
        study_description: 'studyDescription1',

        people_report: {
          people_counters: [
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
          ]
        },
        families_report: {
            families_counters: [{
              counters: [
                {
                  counters: [
                    {
                      pedigree: [
                        ['identifier1', 'id1', 'mother1', 'father1', 'gender1', 'role1', 'color1', ':2,1', true, 'label1', 'smallLabel1']
                      ],
                      pedigrees_count: 5
                    },
                    {
                      pedigree: [
                        [
                          'identifier2', 'id2', 'mother2', 'father2', 'gender2', 'role2', 'color2', ':5,7', false, 'label2', 'smallLabel2'
                        ]
                      ],
                      pedigrees_count: 7
                    }
                  ]
                }, {
                  counters: [
                    {
                      pedigree: [
                        [
                          'identifier3', 'id3', 'mother3', 'father3', 'gender3', 'role3', 'color3', ':6,8', false, 'label3', 'smallLabel3'
                        ]
                      ],
                      pedigrees_count: 1
                    },
                    {
                      pedigree: [
                        ['identifier4', 'id4', 'mother4', 'father4', 'gender4', 'role4', 'color4', ':1,1', true, 'label4', 'smallLabel4']
                      ],
                      pedigrees_count: 10
                    }
                  ]
                }
              ], group_name: 'groupName1', phenotypes: ['pheno1', 'pheno2'], legend: [
                {id: 'id1', name: 'name1', color: 'color1'},
                {id: 'id2', name: 'name2', color: 'color2'}
              ]
          },
          {
              counters: [
                {
                  counters: [
                    {
                      pedigree: [
                        ['identifier5', 'id5', 'mother5', 'father5', 'gender5', 'role5', 'color5', ':2,2', true, 'label5', 'smallLabel5']
                      ],
                      pedigrees_count: 9
                    },
                    {
                      pedigree: [
                        [
                          'identifier6', 'id6', 'mother6', 'father6', 'gender6', 'role6', 'color6', ':51,7', false, 'label6', 'smallLabel6'
                        ]
                      ],
                      pedigrees_count: 85
                    }
                  ]
                }, {
                  counters: [
                    {
                      pedigree: [
                        [
                          'identifier7', 'id7', 'mother7', 'father7', 'gender7', 'role7', 'color7', ':3,3', false, 'label7', 'smallLabel7'
                        ]
                      ],
                      pedigrees_count: 14
                    },
                    {
                      pedigree: [
                        ['identifier8', 'id8', 'mother8', 'father8', 'gender8', 'role8', 'color8', ':16,13', true, 'label8', 'smallLabel8']
                      ],
                      pedigrees_count: 11
                    }
                  ]
                }
              ], group_name: 'groupName2', phenotypes: ['pheno3', 'pheno4'], legend: [
                {id: 'id3', name: 'name3', color: 'color3'},
                {id: 'id4', name: 'name4', color: 'color4'}
              ]
          }],
          families_total: 5
        },
        denovo_report: {
          tables: [
            {
              rows: [
                {
                effect_type: 'effectType1',
                row : [
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
                  row : [
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
                row : [
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
                  row : [
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

    expect(mockVariantReport1).toEqual(mockVariantReport2);
  });
});