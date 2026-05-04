export class UserGroup {
  public static fromJsonArray(jsonArray: object[]): UserGroup[] {
    return jsonArray.map(v => UserGroup.fromJson(v));
  }

  public static fromJson(json: object): UserGroup {
    return new UserGroup(
      json['id'] as number,
      json['name'] as string,
      json['users'] as string[],
      json['datasets'] as Array<{datasetName: string; datasetId: string}>,
    );
  }

  public constructor(
    public id: number,
    public name: string,
    public users: string[],
    public datasets: Array<{datasetName: string; datasetId: string}>
  ) {}
}
