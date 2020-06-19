import { Component, OnInit, SimpleChanges, OnChanges } from '@angular/core';
import { Router } from '@angular/router';

import { BehaviorSubject } from 'rxjs';
// import { Select2OptionData } from 'ng2-select2';

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
  lockedOptions = {
    width: 'style',
    theme: 'bootstrap',
    multiple: true,
    tags: true,
    disabled: true,
  };
  configurationOptions;
  user$ = new BehaviorSubject<User>(new User(0, '', '', [], false));
  groups$ = new BehaviorSubject<UserGroup[]>(null);

  edit = false;

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

  getDefaultGroupsSelect2() {
    return this.getDefaultGroups().map(group => ({
        id: group,
        text: group,
        selected: true,
      }));
  }

  getDefaultGroups() {
    return this.user$.value.getDefaultGroups();
  }

  updateGroups(groups) {
    this.user$.value.groups = groups;
  }


  submit(user: User) {
    this.usersService.createUser(user)
      .take(1)
      .subscribe(() => this.router.navigate(['/management']));
  }

  goBack() {
    this.router.navigate(['/management']);
  }

}
