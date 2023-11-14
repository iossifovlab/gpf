import { Type } from 'class-transformer';

export class AgpTableConfig {
  @Type(() => AgpColumn)
  public columns: AgpColumn[];

  public defaultDataset: string;
  public pageSize: number;
}

export class AgpColumn {
  @Type(() => AgpColumn)
  public columns: AgpColumn[];

  public id: string;
  public displayName: string;
  public sortable: boolean;
  public displayVertical: boolean;
  public clickable: string | null;
  public meta: string | null;

  public parent?: AgpColumn = null;
  public gridColumn?: string = null;
  public gridRow?: string = null;
  public depth?: number = null;

  private visible: boolean;

  public constructor(
    clickable: string,
    columns: AgpColumn[],
    displayName: string,
    displayVertical: boolean,
    id: string,
    meta: string,
    sortable: boolean,
    visibility: boolean
  ) {
    this.clickable = clickable;
    this.columns = columns;
    this.displayName = displayName;
    this.displayVertical = displayVertical;
    this.id = id;
    this.meta = meta;
    this.sortable = sortable;
    this.visibility = visibility;
  }

  public get visibility(): boolean {
    return this.visible;
  }

  public set visibility(input: boolean) {
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
        this.columns.map(child => {
          child.visibility = true;
        });
      }
    }
  }

  public get visibleChildren(): AgpColumn[] {
    return this.columns.filter(column => column.visibility);
  }

  public static leaves(columns: AgpColumn[], parent?: AgpColumn, depth: number = 1): AgpColumn[] {
    const result: AgpColumn[] = [];
    for (const column of columns.filter(c => c.visibility)) {
      column.parent = parent === null || parent === undefined ? null : parent;
      column.depth = depth;
      if (column.visibleChildren.length > 0) {
        result.push(...AgpColumn.leaves(column.visibleChildren, column, depth + 1));
      } else {
        result.push(column);
      }
    }
    return result;
  }

  public get leaves(): AgpColumn[] {
    const result: AgpColumn[] = [];
    for (const column of this.visibleChildren) {
      if (column.columns.length > 0) {
        result.push(...column.leaves);
      } else {
        result.push(column);
      }
    }
    return result;
  }

  public static calculateGridRow(column: AgpColumn, depth: number): void {
    if (column.gridRow !== null) {
      return;
    }
    if (column.parent !== null) {
      column.gridRow = column.parent.parent !== null ? depth.toString() : `2 / ${depth + 1}`;
      AgpColumn.calculateGridRow(column.parent, depth - 1);
    } else {
      column.gridRow = column.columns.length !== 0 ? '1' : `1 / ${depth + 1}`;
    }
  }

  public static calculateGridColumn(column: AgpColumn): void {
    const leaves = column.leaves.filter(c => c.visibility);
    if (leaves.length === 0) {
      return;
    }
    let endColIdx = leaves[leaves.length - 1].gridColumn;
    if (leaves.length > 1) {
      endColIdx = (Number(endColIdx) + 1).toString();
    }
    column.gridColumn = `${leaves[0].gridColumn} / ${endColIdx}`;
    for (const child of column.visibleChildren.filter(col => col.columns.length > 0)) {
      AgpColumn.calculateGridColumn(child);
    }
  }
}
