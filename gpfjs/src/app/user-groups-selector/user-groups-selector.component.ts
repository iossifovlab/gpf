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
export class UserGroupsSelectorComponent implements OnInit, DoCheck, OnChanges {
  configurationOptions: Select2Options;
  data: Select2OptionData[];
  @ViewChild('selector') selector: Select2Component;

  @Input() groups: UserGroup[];
  // @Input() user: User;
  @Output() groupsChange = new EventEmitter(true);
  private lastEmail = '';
  private element: JQuery;

  @Input() alwaysSelectedGroups: string[] = [];
  @Input() selected: string[] = [];

  constructor() { }

    ngOnChanges(changes: SimpleChanges) {
      if ('alwaysSelectedGroups' in changes && this.element) {
        let prev = changes.alwaysSelectedGroups.previousValue;
        let curr = changes.alwaysSelectedGroups.currentValue;
        
        if (curr.length != prev.length || curr.some((v,i)=> v !== prev[i])) {
          console.log("updating with", this.element.val());

          this.changeSelectedGroups(this.element.val());
        }
      }
    }

    ngDoCheck() {
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
          selected: this.selected.indexOf(group) !== -1
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
    return this.alwaysSelectedGroups;
    // ['any_user', this.user.email];
  }

  filterProtectedGroups(groups: string[]) {
    return groups.filter(group =>
      this.getProtectedGroups().indexOf(group) === -1);
  }

}
