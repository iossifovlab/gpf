export class DatasetPermissions {
  public constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly groups: string[],
    public readonly users: { name: string; email: string }[],
  ) {}

  public static fromJson(json): DatasetPermissions {
    return new DatasetPermissions(
      json['dataset_id'],
      json['dataset_name'],
      json['groups'],
      json['users'],
    );
  }
}
