import { Component, OnInit, HostListener, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
// import { Router, ActivatedRoute } from '@angular/router';
import { UsersService } from './users.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { Observable } from 'rxjs';
import { RegistrationComponent } from '../registration/registration.component';
import { ForgotPasswordComponent } from '../forgot-password/forgot-password.component';
import { share, take } from 'rxjs/operators';

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
  public passwordTimeout = false;
  public loading = false;

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
    this.userInfo$ = this.usersService.getUserInfoObservable().pipe(share());
    this.usersService.emailLog.subscribe(email => {
      this.username = email;
    });
  }

  reloadUserData() {
    this.usersService.getUserInfo().pipe(take(1)).subscribe(() => {
      this.loading = false;
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
          this.showPasswordField = true;
          this.errorMessage = undefined;
        } else {
          this.showPasswordField = false;
          if (res['status'] === 404 || res['status'] === 400) {
            this.errorMessage = 'Invalid email!';
          } else if (res['status'] === 403) {
            this.errorMessage = `Too many incorrect attempts! Please wait ${res['error']['lockout_time']} seconds!`;
          }
        }
    });
  }

  login() {
    this.loading = true;
    this.usersService.login(this.username, this.password).subscribe(
      (res) => {
        if (res === true) {
          this.reloadUserData();
          this.username = null;
          this.password = null;
          this.showPasswordField = false;
          this.errorMessage = undefined;
        } else {
          this.loading = false;
          if (res['status'] === 401) {
            this.passwordTimeout = true;
            setTimeout(() => {
              this.passwordTimeout = false;
              this.showPasswordField = true;
              this.errorMessage = 'Wrong password!';
            }, 1000);
          } else if (res['status'] === 403) {
            this.showPasswordField = false;
            this.errorMessage = `Too many incorrect attempts! Please wait ${res['error']['lockout_time']} seconds!`;
          }
        }

    });
  }

  logout() {
    this.usersService.logout().subscribe( () => { this.reloadUserData(); });
  }

  showRegister() {
    this.usersService.emailLog.next(this.username);
    this.modalService.open(RegistrationComponent);
  }

  showForgotPassword() {
    this.usersService.emailLog.next(this.username);
    this.modalService.open(ForgotPasswordComponent);
  }

  @HostListener('document:click', ['$event'])
  onClick(event) {
    if (
      !event
        .composedPath()
        .find(
          element =>
            element.id === 'login-window' ||
            element.id === 'login-dropdown-toggle-button'
        )
    ) {
      this.hideDropdown = true;
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
