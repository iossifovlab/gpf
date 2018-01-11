import { Pipe, PipeTransform } from '@angular/core';
import { UsersService } from './users.service';

@Pipe({
  name: 'userInfo',
  pure: false
})
export class UserInfoPipe implements PipeTransform {

  constructor(private usersService: UsersService) { }

  transform(input: string) {
    let result = this.usersService.cachedUserInfo()
    return result;
  }
}
