import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { BehaviorSubject } from 'rxjs';
import { Select2OptionData } from 'ng2-select2';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { UserGroup } from '../users-groups/users-groups';

@Component({
  selector: 'gpf-users-create',
  templateUrl: '../user-edit/user-edit.component.html',
  styleUrls: ['../user-edit/user-edit.component.css']
})
export class UserCreateComponent implements OnInit {
  emailValue = '';
  configurationOptions: Select2Options;
  user$ = new BehaviorSubject<User>(new User(0, '', '', [], false));
  groups$ = new BehaviorSubject<UserGroup[]>(null);

  emailEditable = true;

  constructor(
    private router: Router,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  ngOnInit() {
      this.usersGroupsService
        .getAllGroups()
        .take(1)
        .subscribe(groups => this.groups$.next(groups));

      this.configurationOptions = {
        multiple: true,
        theme: 'bootstrap',
        width: '100%',
        allowClear: true,
      };
  }


  groupsToOptions(groups: UserGroup[]) {
    if (!groups) {
      return null;
    }
    return groups.map(group => {
      return {
        id: group.id.toString(),
        text: group.name
      } as Select2OptionData;
    });
  }


  // changeSelectedGroups(change) {
  //   if (this.user$.value && this.groups$.value) {
  //     if (this.user$.value.groups.length !== change.value.length) {
  //       this.user$.value.groups = this.groups$.value
  //         .filter(group => change.value.indexOf(group.id.toString()) !== -1);
  //     }
  //   }
  // }


  submit(user: User) {
    delete user.id;
    user.email = this.emailValue;
    this.usersService.createUser(user)
      .take(1)
      .subscribe(() => this.router.navigate(['/management']));
  }

}
