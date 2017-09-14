import { Component, OnInit, NgZone, Input } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { Observable, ReplaySubject } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css']
})
export class UsersTableComponent implements OnInit {
  users$: Observable<{}>;
  private input$ = new ReplaySubject<string>(1);

  @Input()
  set search(value: string) {
    this.input$.next(value);
  }

  constructor(
    private zone: NgZone,
    private router: Router,
    private route: ActivatedRoute,
    private usersService: UsersService
  ) { }

  ngOnInit() {
    this.users$ = this.input$
      .map(searchTerm => searchTerm.trim())
      .debounceTime(300)
      .distinctUntilChanged()
      .switchMap(searchTerm =>
        this.usersService.searchUsersByGroup(searchTerm))
      .share();

    // this.input$.next(' ');
  }

  deleteUser(user: User) {
    this.usersService.deleteUser(user).take(1)
      .subscribe(() => {
        this.zone.runOutsideAngular(() => {
          window.location.reload();
        });
      });
  }

}
