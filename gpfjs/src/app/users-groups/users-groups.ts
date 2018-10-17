export class UserGroup {

  static fromJsonArray(jsonArray: any[]) {
    return jsonArray.map(v => UserGroup.fromJson(v));
  }

  static fromJson(json) {
    return new UserGroup(
      json['id'],
      json['name'],
      json['users'],
      json['datasets'],
    );
  }

  constructor(
    public id: number,
    public name: string,
    public users: string[],
    public datasets: string[]
  ) {}

}
