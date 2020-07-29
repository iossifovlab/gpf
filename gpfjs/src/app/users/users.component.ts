import { Component, OnInit, HostListener, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
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
  private loginError = false;
  hideDropdown = true;
  userInfo$: Observable<any>;


  @ViewChild('dropdownButton') dropdownButton: ElementRef;
  @ViewChild('dialog') dialog: ElementRef;
  @ViewChild('emailInput') emailInput: ElementRef;

  constructor(
    private modalService: NgbModal,
    private usersService: UsersService,
    private router: Router,
    private currentRoute: ActivatedRoute,
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

  login() {
    this.usersService.login(this.username, this.password).subscribe(
      (res) => {
        if (res) {
          this.reloadUserData();
          this.username = null;
          this.password = null;
          this.loginError = false;
        } else {
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

  focusEmailInput() {
    this.changeDetectorRef.detectChanges();
    this.emailInput.nativeElement.focus();
  }
}
