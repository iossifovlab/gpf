import { User } from '../users/users';

export class SelectableUser {
  constructor(public user: User, public selected = true) { }
}
