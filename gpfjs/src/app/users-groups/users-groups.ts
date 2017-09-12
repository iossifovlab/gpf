export class UserGroup {
  constructor(
    public id: number,
    public name: string,
    public users: string[],
    public datasets: string[]
  ) {}
}
