import { Dataset } from '../datasets/datasets';

export class DatasetTableRow {
  constructor(
    readonly dataset: Dataset,
    readonly groups: string[],
    readonly users: { name: string, email: string }[],
  ) {}
}
