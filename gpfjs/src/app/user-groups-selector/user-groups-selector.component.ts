import { Component, OnInit, Input, EventEmitter, Output } from '@angular/core';

import { Select2OptionData } from 'ng2-select2';

import { User } from '../users/users';
import { UserGroup } from '../users-groups/users-groups';

@Component({
  selector: 'gpf-user-groups-selector',
  templateUrl: './user-groups-selector.component.html',
  styleUrls: ['./user-groups-selector.component.css']
})
export class UserGroupsSelectorComponent implements OnInit {
  configurationOptions: Select2Options;
  data: Select2OptionData[];

  @Input()
  groups: UserGroup[];

  @Input()
  user: User;

  @Output()
  groupsChange = new EventEmitter();

  constructor() { }

  ngOnInit() {

    this.configurationOptions = {
      width: 'style',
      theme: 'bootstrap',
      multiple: true,
      tags: true,
      allowClear: true,
    };

    this.data = this.toSelectOptions(this.groups);
  }

  toSelectOptions(groups: UserGroup[]) {
    return this.filterProtectedGroups(groups.map(group => group.name))
      .map(group => {
        return {
          id: group,
          text: group,
          selected: this.user.groups.indexOf(group) !== -1
        } as Select2OptionData;
      });
  }

  changeSelectedGroups(groups) {
    let event = groups.slice().concat(this.getProtectedGroups());
    this.groupsChange.next(event);
  }

  getProtectedGroups() {
    return ['any_user', this.user.email];
  }

  filterProtectedGroups(groups: string[]) {
    return groups.filter(group =>
      this.getProtectedGroups().indexOf(group) === -1);
  }

}
