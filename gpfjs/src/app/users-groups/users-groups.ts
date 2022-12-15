export class UserGroup {
  public static fromJsonArray(jsonArray: object[]): UserGroup[] {
    return jsonArray.map(v => UserGroup.fromJson(v));
  }

  public static fromJson(json): UserGroup {
    return new UserGroup(
      json['id'],
      json['name'],
      json['users'],
      json['datasets'],
    );
  }

  public constructor(
    public id: number,
    public name: string,
    public users: string[],
    public datasets: Array<{datasetName: string; datasetId: string}>
  ) {}
}
