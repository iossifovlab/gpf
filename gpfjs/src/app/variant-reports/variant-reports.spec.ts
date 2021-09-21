import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import {
  ChildrenCounter,
  GroupCounter,
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
        'smallLabel'
    )], 5);

    const pedigreeCounter2 = PedigreeCounter.fromArray({
        pedigree: [
            ['identifier', 'id', 'mother', 'father', 'gender', 'role', 'color', ':5,7', true, 'label', 'smallLabel']
        ],
        pedigrees_count: 5
    });

    expect(pedigreeCounter as PedigreeCounter).toEqual(pedigreeCounter2 as PedigreeCounter);
  });
});
