import {
  Component, OnInit, Input, Output, EventEmitter, ViewChild, ChangeDetectorRef, ElementRef
} from '@angular/core';
import { UserGroup } from '../users-groups/users-groups';
import { IDropdownSettings } from 'ng-multiselect-dropdown';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-user-groups-selector',
  templateUrl: './user-groups-selector.component.html',
  styleUrls: ['./user-groups-selector.component.css']
})
export class UserGroupsSelectorComponent implements OnInit {
  @Input() public allInputtedGroups: UserGroup[];
  @Input() public defaultGroups: string[] = [];
  @Input() public userGroups;
  public _displayedGroups;
  @Output() public createGroupEvent = new EventEmitter<string>();
  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
  @ViewChild('groupInput') public groupInputRef: ElementRef;

  public data: object[];
  public dropdownSettings: IDropdownSettings = {};

  public constructor(
    private changeDetectorRef: ChangeDetectorRef
  ) { }

  public ngOnInit(): void {
    this.dropdownSettings = {
      idField: 'id',
      textField: 'text',
      allowSearchFilter: true
    };

    this.data = this.groupsToOptions(this.allInputtedGroups);
    if (this.defaultGroups.length !== 0) {
      this._displayedGroups = this.filterOutDefaultGroups(this.userGroups);
    }
  }

  private groupsToOptions(groups: UserGroup[]) {
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

  private filterOutDefaultGroups(groups: string[]) {
    return groups.filter(group =>
      this.defaultGroups.indexOf(group) === -1);
  }

  public createGroup(group: string): void {
    if (!group) {
      return;
    }

    this.data.push({id: group, text: group});
    this.data = [...this.data];

    this.ngbDropdownMenu.dropdown.close();
    this.groupInputRef.nativeElement.value = '';
  }

  public focusGroupNameInput(): void {
    this.changeDetectorRef.detectChanges();
    this.groupInputRef.nativeElement.focus();
  }

  public get displayedGroups() {
    const groupsArray = [];

    if (!this._displayedGroups) {
      return;
    }

    for (const group of this._displayedGroups) {
      groupsArray.push(group.text);
    }

    return groupsArray;
  }
}
