import { plainToClass } from 'class-transformer';
import { AgpTableConfig, AgpColumn } from './autism-gene-profiles-table';

const column1 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 1',
  displayVertical: false,
  id: 'column1',
  meta: null,
  sortable: false,
  visible: true
};

const column21 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 21',
  displayVertical: false,
  id: 'column21',
  meta: null,
  sortable: false,
  visible: true
};

const column22 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 22',
  displayVertical: false,
  id: 'column22',
  meta: null,
  sortable: false,
  visible: true
};

const column2 = {
  clickable: 'createTab',
  columns: [column21, column22],
  displayName: 'column 2',
  displayVertical: false,
  id: 'column2',
  meta: null,
  sortable: false,
  visible: true
};

const column311 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 311',
  displayVertical: false,
  id: 'column311',
  meta: null,
  sortable: false,
  visible: true
};

const column312 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 312',
  displayVertical: false,
  id: 'column312',
  meta: null,
  sortable: false,
  visible: true
};

const column31 = {
  clickable: 'createTab',
  columns: [column311, column312],
  displayName: 'column 31',
  displayVertical: false,
  id: 'column31',
  meta: null,
  sortable: false,
  visible: true
};

const column321 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 321',
  displayVertical: false,
  id: 'column321',
  meta: null,
  sortable: false,
  visible: true
};

const column322 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 322',
  displayVertical: false,
  id: 'column322',
  meta: null,
  sortable: false,
  visible: true
};

const column32 = {
  clickable: 'createTab',
  columns: [column321, column322],
  displayName: 'column 32',
  displayVertical: false,
  id: 'column32',
  meta: null,
  sortable: false,
  visible: true
};

const column3 = {
  clickable: 'createTab',
  columns: [column31, column32],
  displayName: 'column 3',
  displayVertical: false,
  id: 'column3',
  meta: null,
  sortable: false,
  visible: true
};

describe('AgpTableConfig', () => {
  let config: AgpTableConfig;
  /*
   *  Column1
   *
   *  Column2
   *    |
   *    |__Column21
   *    |__Column22
   *
   *  Column3
   *    |
   *    |__Column31
   *    |     |
   *    |     |__Column311
   *    |     |__Column312
   *    |
   *    |__Column32
   *          |
   *          |__Column321
   *          |__Column322
   */

  beforeEach(() => {
    config = plainToClass(AgpTableConfig, {
      defaultDataset: 'dataset1',
      pageSize: 3,
      columns: [
        column1,
        column2,
        column3
      ]
    });
  });

  it('should set column visibility', () => {
    AgpColumn.leaves(config.columns);

    // Basic visibility
    config.columns[0].visibility = false;
    expect(config.columns[0].visibility).toBeFalsy();
    config.columns[0].visibility = true;
    expect(config.columns[0].visibility).toBeTruthy();

    // Parent visibility when children change
    config.columns[2].columns[0].visibility = false;
    expect(config.columns[2].visibility).toBeTruthy();

    config.columns[2].columns[0].visibility = false;
    config.columns[2].columns[1].visibility = false;
    expect(config.columns[2].visibility).toBeFalsy();

    // Children visibility when parent change
    config.columns[2].columns[0].columns[0].visibility = false;
    config.columns[2].columns[0].columns[1].visibility = false;
    config.columns[2].columns[0].visibility = true;
    expect(config.columns[2].columns[0].columns[0].visibility).toBeTruthy();
    expect(config.columns[2].columns[0].columns[1].visibility).toBeTruthy();
  });

  it('should get visible children', () => {
    AgpColumn.leaves(config.columns);

    // 2 children visible
    config.columns[2].columns[0].columns[0].visibility = true;
    config.columns[2].columns[0].columns[1].visibility = true;
    let expectedChildren = [
      config.columns[2].columns[0].columns[0],
      config.columns[2].columns[0].columns[1]
    ];
    expect(config.columns[2].columns[0].columns[0].parent.visibleChildren).toStrictEqual(expectedChildren);
    expect(config.columns[2].columns[0].columns[1].parent.visibleChildren).toStrictEqual(expectedChildren);
    expect(config.columns[2].columns[0].visibleChildren).toStrictEqual(expectedChildren);

    // Frist child visible
    config.columns[2].columns[0].columns[0].visibility = false;
    config.columns[2].columns[0].columns[1].visibility = true;
    expectedChildren = [
      config.columns[2].columns[0].columns[1]
    ];
    expect(config.columns[2].columns[0].columns[0].parent.visibleChildren).toStrictEqual(expectedChildren);
    expect(config.columns[2].columns[0].columns[1].parent.visibleChildren).toStrictEqual(expectedChildren);
    expect(config.columns[2].columns[0].visibleChildren).toStrictEqual(expectedChildren);

    // Second child visible
    config.columns[2].columns[0].columns[0].visibility = true;
    config.columns[2].columns[0].columns[1].visibility = false;
    expectedChildren = [
      config.columns[2].columns[0].columns[0]
    ];
    expect(config.columns[2].columns[0].columns[0].parent.visibleChildren).toStrictEqual(expectedChildren);
    expect(config.columns[2].columns[0].columns[1].parent.visibleChildren).toStrictEqual(expectedChildren);
    expect(config.columns[2].columns[0].visibleChildren).toStrictEqual(expectedChildren);

    // No children visible
    config.columns[2].columns[0].columns[0].visibility = false;
    config.columns[2].columns[0].columns[1].visibility = false;
    expectedChildren = [];
    expect(config.columns[2].columns[0].columns[0].parent.visibleChildren).toStrictEqual(expectedChildren);
    expect(config.columns[2].columns[0].columns[1].parent.visibleChildren).toStrictEqual(expectedChildren);
    expect(config.columns[2].columns[0].visibleChildren).toStrictEqual(expectedChildren);
  });

  it('should set column parent and depth and get leaves', () => {
    const leaves = AgpColumn.leaves(config.columns);

    expect(config.columns[0].parent).toBeNull();
    expect(config.columns[0].depth).toBe(1);

    expect(config.columns[1].parent).toBeNull();
    expect(config.columns[1].depth).toBe(1);

    expect(config.columns[1].columns[0].parent.id).toBe('column2');
    expect(config.columns[1].columns[0].depth).toBe(2);

    expect(config.columns[1].columns[1].parent.id).toBe('column2');
    expect(config.columns[1].columns[1].depth).toBe(2);

    expect(config.columns[2].parent).toBeNull();
    expect(config.columns[2].depth).toBe(1);

    expect(config.columns[2].columns[0].parent.id).toBe('column3');
    expect(config.columns[2].columns[0].depth).toBe(2);

    expect(config.columns[2].columns[0].columns[0].parent.id).toBe('column31');
    expect(config.columns[2].columns[0].columns[0].depth).toBe(3);

    expect(config.columns[2].columns[0].columns[1].parent.id).toBe('column31');
    expect(config.columns[2].columns[0].columns[1].depth).toBe(3);

    expect(config.columns[2].columns[1].parent.id).toBe('column3');
    expect(config.columns[2].columns[1].depth).toBe(2);

    expect(config.columns[2].columns[1].columns[0].depth).toBe(3);
    expect(config.columns[2].columns[1].columns[0].parent.id).toBe('column32');

    expect(config.columns[2].columns[1].columns[1].depth).toBe(3);
    expect(config.columns[2].columns[1].columns[1].parent.id).toBe('column32');

    expect(leaves[0]).toStrictEqual(config.columns[0]);
    expect(leaves[1]).toStrictEqual(config.columns[1].columns[0]);
    expect(leaves[2]).toStrictEqual(config.columns[1].columns[1]);
    expect(leaves[3]).toStrictEqual(config.columns[2].columns[0].columns[0]);
    expect(leaves[4]).toStrictEqual(config.columns[2].columns[0].columns[1]);
    expect(leaves[5]).toStrictEqual(config.columns[2].columns[1].columns[0]);
    expect(leaves[6]).toStrictEqual(config.columns[2].columns[1].columns[1]);
  });

  it('should get column leaves', () => {
    expect(config.columns[0].leaves).toStrictEqual([]);
    expect(config.columns[1].leaves).toStrictEqual(config.columns[1].columns);
    expect(config.columns[2].leaves).toStrictEqual(
      config.columns[2].columns[0].columns.concat(config.columns[2].columns[1].columns)
    );
    expect(config.columns[2].columns[1].leaves).toStrictEqual(config.columns[2].columns[1].columns);
  });

  it('should calculate grid row', () => {
    const leaves = AgpColumn.leaves(config.columns);
    const maxDepth = Math.max(...leaves.map(leaf => leaf.depth));

    leaves.forEach(leaf => AgpColumn.calculateGridRow(leaf, maxDepth));

    expect(config.columns[0].gridRow).toBe('1 / 4');
    expect(config.columns[1].gridRow).toBe('1');
    expect(config.columns[1].columns[0].gridRow).toBe('2 / 4');
    expect(config.columns[1].columns[1].gridRow).toBe('2 / 4');
    expect(config.columns[2].gridRow).toBe('1');
    expect(config.columns[2].columns[0].gridRow).toBe('2 / 3');
    expect(config.columns[2].columns[0].columns[0].gridRow).toBe('3');
    expect(config.columns[2].columns[0].columns[1].gridRow).toBe('3');
    expect(config.columns[2].columns[1].gridRow).toBe('2 / 3');
    expect(config.columns[2].columns[1].columns[0].gridRow).toBe('3');
    expect(config.columns[2].columns[1].columns[1].gridRow).toBe('3');
  });

  it('should calculate grid column', () => {
    const leaves = AgpColumn.leaves(config.columns);

    let columnIdx = 0;
    for (const leaf of leaves) {
      leaf.gridColumn = (columnIdx + 1).toString();
      columnIdx++;
    }

    config.columns.forEach(col => AgpColumn.calculateGridColumn(col));

    expect(config.columns[0].gridColumn).toBe('1');
    expect(config.columns[1].gridColumn).toBe('2 / 4');
    expect(config.columns[1].columns[0].gridColumn).toBe('2');
    expect(config.columns[1].columns[1].gridColumn).toBe('3');
    expect(config.columns[2].gridColumn).toBe('4 / 8');
    expect(config.columns[2].columns[0].gridColumn).toBe('4 / 6');
    expect(config.columns[2].columns[0].columns[0].gridColumn).toBe('4');
    expect(config.columns[2].columns[0].columns[1].gridColumn).toBe('5');
    expect(config.columns[2].columns[1].gridColumn).toBe('6 / 8');
    expect(config.columns[2].columns[1].columns[0].gridColumn).toBe('6');
    expect(config.columns[2].columns[1].columns[1].gridColumn).toBe('7');
  });
});
