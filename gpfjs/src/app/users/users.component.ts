import {
  Component, OnInit, HostListener, ViewChild, ElementRef, ChangeDetectorRef, EventEmitter, Output
} from '@angular/core';
import { UsersService } from './users.service';
import { ConfigService } from '../config/config.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { Observable } from 'rxjs';
import { RegistrationComponent } from '../registration/registration.component';
import { ForgotPasswordComponent } from '../forgot-password/forgot-password.component';
import { share, take } from 'rxjs/operators';
import { AuthService } from 'app/auth.service';

@Component({
  selector: 'gpf-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css'],
})
export class UsersComponent implements OnInit {
  public username: string;
  public password: string;
  public passwordTimeout = false;
  public loading = false;
  public errorMessage: string;
  public hideDropdown = true;
  public userInfo$: Observable<any>;
  public showPasswordField = false;

  @ViewChild('dropdownButton') public dropdownButton: ElementRef;
  @ViewChild('dialog') public dialog: ElementRef;
  @ViewChild('emailInput') public emailInput: ElementRef;
  @ViewChild('passwordInput') public passwordInput: ElementRef;

  @Output() public loginDropdownClickEvent = new EventEmitter();

  public constructor(
    private modalService: NgbModal,
    private usersService: UsersService,
    private changeDetectorRef: ChangeDetectorRef,
    private config: ConfigService,
    private authService: AuthService
  ) { }

  public ngOnInit(): void {
    this.reloadUserData();
    this.userInfo$ = this.usersService.getUserInfoObservable().pipe(share());
    this.usersService.emailLog.subscribe(email => {
      this.username = email;
    });
  }

  public reloadUserData(): void {
    this.usersService.getUserInfo().pipe(take(1)).subscribe(() => {
      this.loading = false;
    });
  }

  public back(): void {
    this.showPasswordField = false;
  }

  public login(): void {
    const codeChallenge = this.authService.generatePKCE();
    location.href = `${this.config.rootUrl}/o/authorize/?response_type=code&code_challenge_method=S256&code_challenge=${codeChallenge}&client_id=${this.config.oauthClientId}`;
  }

  public logout(): void {
    this.usersService.logout().subscribe(() => this.reloadUserData());
  }

  public showRegister(): void {
    this.usersService.emailLog.next(this.username);
    this.modalService.open(RegistrationComponent);
  }

  public showForgotPassword(): void {
    this.usersService.emailLog.next(this.username);
    this.modalService.open(ForgotPasswordComponent);
  }

  @HostListener('document:click', ['$event'])
  public onClick(event): void {
    if (
      !event.composedPath().find(
        element => element.id === 'login-window' || element.id === 'login-dropdown-toggle-button'
      )
    ) {
      this.hideDropdown = true;
    }
  }

  public loginDropdownClick(): void {
    this.hideDropdown = !this.hideDropdown;
    this.focusEmailInput();
    this.loginDropdownClickEvent.emit();
  }

  public focusEmailInput(): void {
    this.changeDetectorRef.detectChanges();
    this.emailInput.nativeElement.focus();
  }

  public focusPasswordInput(): void {
    this.waitForPasswordInput().then(() => {
      this.passwordInput.nativeElement.focus();
    });
  }

  private async waitForPasswordInput(): Promise<void> {
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
