import { Type } from 'class-transformer';

export class Column {
  @Type(() => Column)
  public columns: Column[];

  public id: string;
  public displayName: string;
  public visible: boolean;
  public sortable: boolean;

  public parent?: Column;
  public gridColumn?: string;
  public gridRow?: string;
  public depth?: number;

  static leaves(columns: Column[], parent?: Column, depth: number = 0): Column[] {
    const result: Column[] = [];
    for (const column of columns) { 
      if (column.columns.length > 0) {
        result.push(...Column.leaves(column.columns, column, depth + 1))
      } else {
        column.parent = parent ? parent : null;
        column.depth = depth;
        result.push(column)
      }
    }
    return result;
  }
}

export class AgpConfig {
  @Type(() => Column)
  public columns: Column[];
}
