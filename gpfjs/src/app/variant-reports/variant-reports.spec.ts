import {
  ChildrenCounter,
  GroupCounter,
  PeopleCounter,
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

fdescribe('PeopleCounter', () => {
  fit('should create from json', () => {
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

  fit('should get children counter', () => {
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
  });
});
