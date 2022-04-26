import { Dataset } from '../datasets/datasets';

export class DatasetTableRow {
  public constructor(
    public readonly dataset: Dataset,
    public readonly groups: string[],
    public readonly users: { name: string; email: string }[],
  ) {}
}
