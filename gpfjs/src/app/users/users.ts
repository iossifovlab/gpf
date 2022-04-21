export class User {
  public static fromJsonArray(json): User[] {
    return json.map(user => User.fromJson(user));
  }

  public static fromJson(json): User {
    return new User(
      json['id'],
      json['name'],
      json['email'],
      json['groups'],
      json['hasPassword'],
      json['allowedDatasets'],
    );
  }

  public constructor(
    public id: number,
    public name: string,
    public email: string,
    public groups: Array<string>,
    public hasPassword: boolean,
    public allowedDatasets: Array<string>
  ) {}

  public getDefaultGroups(): string[] {
    return ['any_user', this.email];
  }

  public clone(): User {
    return new User(
      this.id,
      this.name,
      this.email,
      this.groups.slice(),
      this.hasPassword,
      this.allowedDatasets
    );
  }
}
