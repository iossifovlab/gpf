export class User {

  static fromJsonArray(json): User[] {
    return json.map(user => User.fromJson(user));
  }

  static fromJson(json) {
    return new User(
      json['id'],
      json['name'],
      json['email'],
      json['groups'],
      json['hasPassword'],
      json['allowedDatasets'],
    );
  }

  constructor(
    public id: number,
    public name: string,
    public email: string,
    public groups: Array<string>,
    public hasPassword: boolean,
    public allowedDatasets: Array<string>
  ) {}

  getDefaultGroups() {
    return ['any_user', this.email];
  }

  clone() {
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
