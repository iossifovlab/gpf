import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { BehaviorSubject } from 'rxjs';
import { Select2OptionData } from 'ng2-select2';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { UserGroup } from '../users-groups/users-groups';
import { UsersGroupsService } from '../users-groups/users-groups.service';

@Component({
  selector: 'gpf-user-edit',
  templateUrl: './user-edit.component.html',
  styleUrls: ['./user-edit.component.css']
})
export class UserEditComponent implements OnInit {
  configurationOptions: Select2Options;
  user$ = new BehaviorSubject<User>(null);
  groups$ = new BehaviorSubject<UserGroup[]>(null);
  emailValue: string;
  initialValue: string[];

  emailEditable = false;

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  ngOnInit() {
    this.route.params.take(1)
      .map(params => +params['id'])
      .switchMap(userId => this.usersService.getUser(userId))
      .subscribe(user => {
        this.emailValue = user.email;
        this.initialValue = this.groupsToValue(user.groups);
        this.user$.next(user);
      });

    this.usersGroupsService
      .getAllGroups()
      .take(1)
      .subscribe(groups => this.groups$.next(groups));



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

  groupsToValue(groups: UserGroup[]) {
    if (!groups) {
      return [];
    }
    return groups.map(group => group.id.toString());
  }

  changeSelectedGroups(change) {
    if (this.user$.value && this.groups$.value) {
      if (this.user$.value.groups.length !== change.value.length) {
        this.user$.value.groups = this.groups$.value
          .filter(group => change.value.indexOf(group.id.toString()) !== -1);
      }
    }
  }

  submit(user) {
    delete user.email;
    this.usersService.updateUser(user)
      .take(1)
      .subscribe(() => this.router.navigate(['/management']));
  }
}
