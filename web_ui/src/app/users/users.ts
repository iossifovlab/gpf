export interface UserInfo {
  email: string;
  isAdministrator: boolean;
  loggedIn: boolean;
}

export class User {
  public static fromJsonArray(json): User[] {
    return json.map(user => User.fromJson(user));
  }

  public static fromJson(json: object): User {
    return new User(
      json['id'] as number,
      json['name'] as string,
      json['email'] as string,
      json['groups'] as Array<string>,
      json['hasPassword'] as boolean,
      json['allowedDatasets'] as Array<{datasetName: string; datasetId: string}>,
    );
  }

  public constructor(
    public id: number,
    public name: string,
    public email: string,
    public groups: Array<string>,
    public hasPassword: boolean,
    public allowedDatasets: Array<{datasetName: string; datasetId: string}>
  ) {}

  public getDefaultGroups(): string[] {
    return ['any_user'];
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

  public sortGroups(): void {
    if (!this.groups) {
      return;
    }
    const defaultGroups = this.groups
      .filter(group => this.getDefaultGroups().indexOf(group) !== -1);
    let otherGroups = this.groups
      .filter(group => this.getDefaultGroups().indexOf(group) === -1);

    if (defaultGroups.length === 2 && defaultGroups[0] !== 'any_user') {
      const group = defaultGroups[0];
      defaultGroups[0] = defaultGroups[1];
      defaultGroups[1] = group;
    }

    otherGroups = otherGroups
      .sort((group1, group2) => group1.localeCompare(group2));

    this.groups = defaultGroups.concat(otherGroups);
  }
}
