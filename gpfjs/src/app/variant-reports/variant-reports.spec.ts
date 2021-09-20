import { ChildrenCounter, GroupCounter } from './variant-reports';

describe('ChildrenCounter', () => {
  it('should create from json', () => {
    const childrenCounter = ChildrenCounter.fromJson(
      {
        column: 'fakeColumn',
        row1: 7
      },
      'row1'
    );

    expect(childrenCounter).toEqual(new ChildrenCounter('row1', 'fakeColumn', 7));
  });
});

describe('GroupCounter', () => {
  it('should create from json', () => {
    const groupCounter = GroupCounter.fromJson(
      {
        column: 'fakeColumn',
        row1: 7,
        row2: 13,
        row3: 17
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
