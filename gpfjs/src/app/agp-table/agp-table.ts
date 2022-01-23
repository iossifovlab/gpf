import { Type } from 'class-transformer';
import * as _ from 'lodash';

export class Column {
  @Type(() => Column)
  public columns: Column[];

  public id: string;
  public displayName: string;
  public visible: boolean;
  public sortable: boolean;

  public parent?: Column = null;
  public gridColumn?: string = null;
  public gridRow?: string = null;
  public depth?: number = null;

  static leaves(columns: Column[], parent?: Column, depth: number = 1): Column[] {
    const result: Column[] = [];
    for (const column of columns) { 
      column.parent = parent ? parent : null;
      column.depth = depth;
      if (column.columns.length > 0) {
        result.push(...Column.leaves(column.columns, column, depth + 1))
      } else {
        result.push(column)
      }
    }
    return result;
  }

  static setGridRow(column: Column, currentRow: number) {
    if (column.gridRow !== null) {
      return;
    }
    if (column.parent !== null) {
      column.gridRow = currentRow.toString();
      Column.setGridRow(column.parent, currentRow - 1);
    } else {
      column.gridRow = `1 / ${currentRow + 1}`;
    }
  }

  static setGridColumn(column: Column) {
    const leaves = Column.leaves([column]);
    let endColIdx = leaves[leaves.length - 1].gridColumn;
    if (leaves.length > 1) {
      endColIdx = (+endColIdx + 1).toString();
    }
    column.gridColumn = `${leaves[0].gridColumn} / ${endColIdx}`;
    for (const child of column.columns.filter(col => col.columns.length > 0)) {
      Column.setGridColumn(child);
    }
  }
}

export class AgpConfig {
  @Type(() => Column)
  public columns: Column[];
}
