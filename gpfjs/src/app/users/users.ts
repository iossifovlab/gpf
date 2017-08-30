import { UserGroup } from '../users-groups/users-groups';

export class User {
  constructor(
    public id: number,
    public email: string,
    public staff: boolean,
    public superuser: boolean,
    public active: boolean,
    public groups: Array<UserGroup>,
    public researcher?: boolean,
    public researcherId?: string
  ) {}
}
