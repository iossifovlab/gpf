import {
  Component, OnInit, Input, EventEmitter, Output, OnChanges, SimpleChanges,
  DoCheck, ViewChild, ElementRef
} from '@angular/core';

import { Select2OptionData, Select2Component } from 'ng2-select2';

import { User } from '../users/users';
import { UserGroup } from '../users-groups/users-groups';

@Component({
  selector: 'gpf-user-groups-selector',
  templateUrl: './user-groups-selector.component.html',
  styleUrls: ['./user-groups-selector.component.css']
})
export class UserGroupsSelectorComponent implements OnInit, DoCheck {
  configurationOptions: Select2Options;
  data: Select2OptionData[];
  @ViewChild('selector') selector: Select2Component;

  @Input() groups: UserGroup[];
  @Input() user: User;
  @Output() groupsChange = new EventEmitter();
  private lastEmail = '';
  private element: JQuery;

  constructor() { }


  ngDoCheck() {
    if (!this.user && this.lastEmail) {
      this.lastEmail = '';
    } else if (this.user && this.user.email !== this.lastEmail) {
      this.changeSelectedGroups(this.element.val());
      this.lastEmail = this.user.email;
    }
  }

  ngOnInit() {
    this.element = jQuery(this.selector.selector.nativeElement);

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
    if (!groups) {
      return;
    }
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
