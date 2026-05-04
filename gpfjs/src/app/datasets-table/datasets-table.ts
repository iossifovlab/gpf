export class DatasetPermissions {
  public constructor(
    public id: string,
    public name: string,
    public groups: string[],
    public users: { name: string; email: string }[],
  ) {}

  public static fromJson(json): DatasetPermissions {
    return new DatasetPermissions(
      json['dataset_id'],
      json['dataset_name'],
      json['groups'],
      json['users'],
    );
  }

  public getDefaultGroups(): string[] {
    return ['any_dataset', this.id];
  }
}
