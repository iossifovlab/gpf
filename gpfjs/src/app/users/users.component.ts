import { Component, OnInit, Inject } from '@angular/core';
import { UsersService } from './users.service';
import { ConfigService } from '../config/config.service';
import { AuthService } from 'app/auth.service';
import { Router } from '@angular/router';
import { APP_BASE_HREF } from '@angular/common';
import { UserInfo } from './users';

@Component({
  selector: 'gpf-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css'],
})
export class UsersComponent implements OnInit {
  public userInfo: UserInfo = null;

  public constructor(
    private usersService: UsersService,
    private config: ConfigService,
    private authService: AuthService,
    private router: Router,
    @Inject(APP_BASE_HREF) private baseHref: string
  ) { }

  public ngOnInit(): void {
    this.userInfo = this.usersService.cachedUserInfo();
  }

  public login(): void {
    const codeChallenge = this.authService.generatePKCE();
    const state = {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      came_from: this.router.url
    };
    window.location.href = `${this.config.rootUrl}${this.baseHref}`
      + 'o/authorize/?response_type=code'
      + '&code_challenge_method=S256'
      + `&code_challenge=${codeChallenge}`
      + '&scope=read'
      + `&client_id=${this.config.oauthClientId}`
      + `&redirect_uri=${window.location.origin}${this.baseHref}login`
      + `&state=${btoa(JSON.stringify(state))}`;
  }

  public logout(): void {
    (document.getElementById("log-out-button") as HTMLButtonElement).disabled = true;
    this.usersService.logout().subscribe(() => {});
  }
}
