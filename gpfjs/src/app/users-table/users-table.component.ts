import { Component, OnInit, Input } from '@angular/core';

import { Observable, ReplaySubject } from 'rxjs';

import { SelectableUser } from '../user-management/user-management';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css']
})
export class UsersTableComponent implements OnInit {

  @Input()
  users: SelectableUser[];

  constructor() { }

  ngOnInit() {
  }

}
