import { Component, OnInit, Inject } from '@angular/core';
import { UsersService } from './users.service';
import { ConfigService } from '../config/config.service';
import { Observable } from 'rxjs';
import { share, take } from 'rxjs/operators';
import { AuthService } from 'app/auth.service';
import { Router } from '@angular/router';
import { APP_BASE_HREF } from '@angular/common';

@Component({
  selector: 'gpf-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css'],
})
export class UsersComponent implements OnInit {
  public userInfo$: Observable<any>;

  public constructor(
    private usersService: UsersService,
    private config: ConfigService,
    private authService: AuthService,
    private router: Router,
    @Inject(APP_BASE_HREF) private baseHref: string
  ) { }

  public ngOnInit(): void {
    this.reloadUserData();
    this.userInfo$ = this.usersService.getUserInfoObservable().pipe(share());
  }

  public reloadUserData(): void {
    this.usersService.getUserInfo().pipe(take(1)).subscribe();
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
    this.usersService.logout().subscribe(() => this.reloadUserData());
  }
}
