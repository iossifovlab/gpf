export class UserGroup {

  static fromJsonArray(jsonArray: any) {
    return jsonArray as UserGroup[];
  }

  constructor(
    public id: number,
    public name: string,
    public users: string[],
    public datasets: string[]
  ) {}

}
