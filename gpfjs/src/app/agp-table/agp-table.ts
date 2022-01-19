import { Type } from 'class-transformer';

export class Column {
  @Type(() => Column)
  public columns: Column[];

  public id: string;
  public index?: number;
  public displayName: string;
  public visible: boolean;
  public sortable: boolean;
}

export class AgpConfig {
  @Type(() => Column)
  public columns: Column[];
}
