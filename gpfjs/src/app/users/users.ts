export class User {
  constructor(
    public id: number,
    public name: string,
    public email: string,
    public groups: Array<string>,
    public hasPassword: boolean
  ) {}
}
