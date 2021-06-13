import { Component, OnInit, HostListener, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
// import { Router, ActivatedRoute } from '@angular/router';
import { UsersService } from './users.service';
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
  errorMessage: string;
  hideDropdown = true;
  userInfo$: Observable<any>;
  showPasswordField = false;

  @ViewChild('dropdownButton') dropdownButton: ElementRef;
  @ViewChild('dialog') dialog: ElementRef;
  @ViewChild('emailInput') emailInput: ElementRef;
  @ViewChild('passwordInput') passwordInput: ElementRef;

  constructor(
    private modalService: NgbModal,
    private usersService: UsersService,
    // private router: Router,
    // private currentRoute: ActivatedRoute,
    private changeDetectorRef: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.reloadUserData();
    this.userInfo$ = this.usersService.getUserInfoObservable().share();
  }

  reloadUserData() {
    this.usersService.getUserInfo()
      .take(1)
      .subscribe(() => {
        // this.router.navigate(['.'], { relativeTo: this.currentRoute });
      });
  }

  back() {
    this.showPasswordField = false;
  }

  next() {
    this.usersService.login(this.username).subscribe(
      (res) => {
        if (res === true) {
          this.reloadUserData();
          this.showPasswordField = true;
          this.errorMessage = undefined;
        } else {
          this.showPasswordField = false;
          if (res['status'] === 404) {
            this.errorMessage = 'Wrong username!';
          } else if (res['status'] === 403) {
            this.errorMessage = `Too many incorrect attempts! Please wait ${res['error']['lockout_time']} seconds!`;
          }
        }
    });
  }

  login() {
    this.usersService.login(this.username, this.password).subscribe(
      (res) => {
        if (res === true) {
          this.reloadUserData();
          this.username = null;
          this.password = null;
          this.showPasswordField = false;
          this.errorMessage = undefined;
        } else {
          if (res['status'] === 401) {
            this.showPasswordField = true;
            this.errorMessage = 'Wrong password!';
          } else if (res['status'] === 403) {
            this.showPasswordField = false;
            this.errorMessage = `Too many incorrect attempts! Please wait ${res['error']['lockout_time']} seconds!`;
          }
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
    console.log();
    if (this.dialog && this.dropdownButton
      && event.path[0]['id'] !== 'next-button'
      && event.path[0]['id'] !== 'back-button') {
      if (!this.dialog.nativeElement.contains(event.target) &&
      !this.dropdownButton.nativeElement.contains(event.target)) {
        this.hideDropdown = true;
      }
    }
  }

  focusEmailInput() {
    this.changeDetectorRef.detectChanges();
    this.emailInput.nativeElement.focus();
  }

  focusPasswordInput() {
    this.waitForPasswordInput().then(() => {
      this.passwordInput.nativeElement.focus();
    });
  }

  async waitForPasswordInput() {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.passwordInput !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 100);
    });
  }
}
