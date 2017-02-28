import { Component, OnInit } from '@angular/core';
import { UsersService } from './users.service';
import { Store } from '@ngrx/store';
import { USER_LOGIN, USER_LOGOUT } from './users-store'

@Component({
  selector: 'gpf-users',
  templateUrl: './users.component.html',
})
export class UsersComponent implements OnInit {
  private username = "admin@iossifovlab.com";
  private password = "secret";
  private displayedUsername: string;

  constructor(
    private store: Store<any>,
    private usersService: UsersService
  ) { }

  ngOnInit() {
    this.reloadUserData();
  }

  reloadUserData() {
    this.usersService.getUserInfo().subscribe(
      (username) => {
        this.displayedUsername = username;
        /*this.store.dispatch({
          'type': username ? USER_LOGIN : USER_LOGOUT,
        });*/
    });
  }

  login() {
    this.usersService.login(this.username, this.password).subscribe(
      (res) => {
        this.reloadUserData();
    });
  }

  logout() {
    this.usersService.logout().subscribe(
      (res) => {
        this.reloadUserData();
    });
  }

}
