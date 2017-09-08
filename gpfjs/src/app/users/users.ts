import { UserGroup } from '../users-groups/users-groups';

export class User {
  constructor(
    public id: number,
    public name: string,
    public email: string,
    public groups: Array<UserGroup>,
    public hasPassword: boolean
  ) {}
}
