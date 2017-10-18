import { Component, OnInit, HostListener, ViewChild, ElementRef } from '@angular/core';
import { UsersService } from './users.service';
import { Store } from '@ngrx/store';
import { USER_LOGIN, USER_LOGOUT } from './users-store'
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { Observable } from 'rxjs';
import { RegistrationComponent } from '../registration/registration.component';
import { ForgotPasswordComponent } from '../forgot-password/forgot-password.component';

@Component({
  selector: 'gpf-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css'],
})
export class UsersComponent implements OnInit {
  private username;
  private password;
  private loginError = false;
  hideDropdown = true;
  userInfo$: Observable<any>;


  @ViewChild('dropdownButton') dropdownButton: ElementRef;
  @ViewChild('dialog') dialog: ElementRef;

  constructor(
    private modalService: NgbModal,
    private store: Store<any>,
    private usersService: UsersService
  ) { }

  ngOnInit() {
    this.reloadUserData();
    this.userInfo$ = this.usersService.getUserInfoObservable().share();
  }

  reloadUserData() {
    this.usersService.getUserInfo().subscribe(
      (userData) => {
        this.store.dispatch({
          'type': userData.loggedIn ? USER_LOGIN : USER_LOGOUT,
        });
    });
  }

  login() {
    this.usersService.login(this.username, this.password).subscribe(
      (res) => {
        if (res) {
          this.reloadUserData();
          this.username = null;
          this.password = null;
          this.loginError = false;
        }
        else {
          this.loginError = true;
        }

    });
  }

  logout() {
    this.usersService.logout().subscribe(
      (res) => {
        this.reloadUserData();
    });
  }


  showRegister() {
    this.modalService.open(RegistrationComponent);
  }

  showForgotPassword() {
    this.modalService.open(ForgotPasswordComponent);
  }

  @HostListener('document:click', ['$event'])
  onClick(event) {
    if (this.dialog && this.dropdownButton) {
      if (!this.dialog.nativeElement.contains(event.target) &&
      !this.dropdownButton.nativeElement.contains(event.target)) {
        this.hideDropdown = true;
      }
    }
  }

}
