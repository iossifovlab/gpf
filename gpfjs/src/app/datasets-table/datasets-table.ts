

export class DatasetTableRow {
  constructor(
    readonly dataset: string,
    readonly groups: string[],
    readonly users: { name: string, email: string }[],
  ) {}
}
