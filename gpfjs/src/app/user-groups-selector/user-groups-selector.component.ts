import { Component, OnInit, Input, Output, EventEmitter, ViewChild, ChangeDetectorRef, ElementRef } from '@angular/core';
import { UserGroup } from '../users-groups/users-groups';
import { IDropdownSettings } from 'ng-multiselect-dropdown';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-user-groups-selector',
  templateUrl: './user-groups-selector.component.html',
  styleUrls: ['./user-groups-selector.component.css']
})
export class UserGroupsSelectorComponent implements OnInit {
  @Input() allInputtedGroups: UserGroup[];
  @Input() defaultGroups: string[] = [];
  @Input() _selectedGroups;
  @Output() createGroupEvent = new EventEmitter<string>();
  @ViewChild(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu;
  @ViewChild('groupInput') groupInputRef: ElementRef;

  data: object;
  dropdownSettings: IDropdownSettings = {};

  constructor(
    private changeDetectorRef: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.dropdownSettings = {
      idField: 'id',
      textField: 'text',
      allowSearchFilter: true
    };

    this.data = this.groupsToOptions(this.allInputtedGroups);
    if (this.defaultGroups.length !== 0) {
      this._selectedGroups = this.filterOutDefaultGroups(this._selectedGroups);
    }
  }

  groupsToOptions(groups: UserGroup[]) {
    if (!groups) {
      return null;
    }

    groups.forEach(element => {
      if (element.name === 'any_user') {
        groups.splice(groups.indexOf(element), 1);
      }
    });

    return groups.map(group => {
      return {
        id: group.name,
        text: group.name
      };
    });
  }

  filterOutDefaultGroups(groups: string[]) {
    return groups.filter(group =>
      this.defaultGroups.indexOf(group) === -1);
  }

  createGroup(group: string) {
    if (!group) {
      return;
    }

    this.createGroupEvent.emit(group);
    this.ngbDropdownMenu.dropdown.close();
    this.groupInputRef.nativeElement.value = '';
  }

  focusGroupNameInput() {
    this.changeDetectorRef.detectChanges();
    this.groupInputRef.nativeElement.focus();
  }

  get selectedGroups() {
    const groupsArray = [];

    if (!this._selectedGroups) {
      return;
    }

    for (const group of this._selectedGroups) {
      groupsArray.push(group.text);
    }

    return groupsArray;
  }
}
