import { Component, OnInit } from '@angular/core';

import { Observable } from 'rxjs';

import { UserGroup } from '../users-groups/users-groups';
import { UsersGroupsService } from '../users-groups/users-groups.service';

@Component({
  selector: 'gpf-groups-table',
  templateUrl: './groups-table.component.html',
  styleUrls: ['./groups-table.component.css']
})
export class GroupsTableComponent implements OnInit {

  constructor(
    private usersGroupsService: UsersGroupsService
  ) { }

  groups$: Observable<UserGroup[]>;

  ngOnInit() {
    this.groups$ = this.usersGroupsService.getAllGroups();
  }

}
