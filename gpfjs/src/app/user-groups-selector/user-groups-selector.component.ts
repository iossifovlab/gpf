import { Component, OnInit, Input, EventEmitter, Output } from '@angular/core';
import { UserGroup } from '../users-groups/users-groups';
import { IDropdownSettings } from 'ng-multiselect-dropdown';

@Component({
  selector: 'gpf-user-groups-selector',
  templateUrl: './user-groups-selector.component.html',
  styleUrls: ['./user-groups-selector.component.css']
})
export class UserGroupsSelectorComponent implements OnInit {
  data: object;
  groupsArray: string[] = [];
  dropdownSettings: IDropdownSettings = {};

  @Input() groups: UserGroup[];
  @Output() groupsChange = new EventEmitter(true);
  @Input() alwaysSelectedGroups: string[] = [];
  @Input() selected: string[] = [];

  constructor() { }

  ngOnInit() {
    this.dropdownSettings = {
      idField: 'id',
      textField: 'text',
      allowSearchFilter: true
    };

    this.data = this.toSelectOptions(this.groups);
  }

  toSelectOptions(groups: UserGroup[]) {
    return this.filterProtectedGroups(groups.map(group => group.name))
      .map(group => {
        return {
          id: group,
          text: group,
          selected: this.selected.indexOf(group) !== -1
        };
      });
  }

  changeSelectedGroups(group) {
    this.groupsArray.push(group.text);
    this.groupsChange.next(this.groupsArray.slice().concat(this.getProtectedGroups()));
  }

  getProtectedGroups() {
    return this.alwaysSelectedGroups;
    // ['any_user', this.user.email];
  }

  filterProtectedGroups(groups: string[]) {
    return groups.filter(group =>
      this.getProtectedGroups().indexOf(group) === -1);
  }
}
