import { Type } from 'class-transformer';

export class AgpTableConfig {
  public defaultDataset: string;
  @Type(() => Column)
  public columns: Column[];
  public pageSize: number;
}

export class Column {
  @Type(() => Column)
  public columns: Column[];

  private visible: boolean;

  public id: string;
  public displayName: string;
  public sortable: boolean;
  public displayVertical: boolean;
  public clickable: string | null;
  public meta: string | null;

  public parent?: Column = null;
  public gridColumn?: string = null;
  public gridRow?: string = null;
  public depth?: number = null;

  get visibility(): boolean {
    return this.visible;
  }

  set visibility(input: boolean) {
    this.visible = input;
    if (!this.visible) {
      if (this.parent !== null && this.parent.visibleChildren.length === 0) {
        this.parent.visibility = false;
      }
    } else {
      if (this.parent !== null && this.parent.visibleChildren.length === 1) {
        this.parent.visibility = true;
      }
      if (this.visibleChildren.length === 0) {
        this.columns.map(child => child.visibility = true);
      }
    }
  }

  get visibleChildren(): Column[] {
    return this.columns.filter(column => column.visibility);
  }

  static leaves(columns: Column[], parent?: Column, depth: number = 1): Column[] {
    const result: Column[] = [];
    for (const column of columns.filter(c => c.visibility)) { 
      column.parent = (parent === null || parent === undefined) ? null : parent;
      column.depth = depth;
      if (column.visibleChildren.length > 0) {
        result.push(...Column.leaves(column.visibleChildren, column, depth + 1))
      } else {
        result.push(column)
      }
    }
    return result;
  }

  get leaves(): Column[] {
    const result: Column[] = [];
    for (const column of this.visibleChildren) {
      if (column.columns.length > 0) {
        result.push(...column.leaves);
      } else {
        result.push(column)
      }
    }
    return result;
  }

  static calculateGridRow(column: Column, depth: number) { 
    if (column.gridRow !== null) {
      return;
    }
    if (column.parent !== null) {
      column.gridRow = column.parent.parent !== null ? depth.toString() : `2 / ${depth + 1}`;
      Column.calculateGridRow(column.parent, depth - 1);
    } else {
      column.gridRow = column.columns.length !== 0 ? '1' : `1 / ${depth + 1}`
    }
  }

  static calculateGridColumn(column: Column) {
    const leaves = column.leaves.filter(c => c.visibility);
    if (leaves.length === 0) {
      return;
    }
    let endColIdx = leaves[leaves.length - 1].gridColumn;
    if (leaves.length > 1) {
      endColIdx = (+endColIdx + 1).toString();
    }
    column.gridColumn = `${leaves[0].gridColumn} / ${endColIdx}`;
    for (const child of column.visibleChildren.filter(col => col.columns.length > 0)) {
      Column.calculateGridColumn(child);
    }
  }
}