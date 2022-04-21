import { Pipe, PipeTransform } from '@angular/core';
import { UsersService } from './users.service';

@Pipe({
  name: 'userInfo',
  pure: false
})
export class UserInfoPipe implements PipeTransform {
  public constructor(private usersService: UsersService) { }
  public transform(input: string) {
    return this.usersService.cachedUserInfo();
  }
}
