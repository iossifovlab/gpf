import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import {
  ChildrenCounter,
  FamilyCounter,
  FamilyCounters,
  GroupCounter,
  Legend,
  LegendItem,
  PedigreeCounter,
  PeopleCounter,
  PeopleReport,
} from './variant-reports';

describe('ChildrenCounter', () => {
  it('should create from json', () => {
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
  it('should create from json', () => {
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
  it('should create from json', () => {
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

  it('should get children counter', () => {
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
  it('should report people data', () => {
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
  it('should create from json', () => {

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
  it('should create from json', () => {
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
  it('should create from json', () => {
    const mockFamilyCounters1 = new FamilyCounters([
        new FamilyCounter([
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
        ]),
        new FamilyCounter([
          new PedigreeCounter([
            new PedigreeData(
              'identifier3',
              'id3',
              'mother3',
              'father3',
              'gender3',
              'role3',
              'color3',
              [6, 8],
              false,
              'label3',
              'smallLabel3')], 1),
          new PedigreeCounter([
            new PedigreeData(
              'identifier4',
              'id4',
              'mother4',
              'father4',
              'gender4',
              'role4',
              'color4',
              [1, 1],
              true,
              'label4',
              'smallLabel4')], 10)
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
