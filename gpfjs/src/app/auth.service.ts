import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from './config/config.service';
import { Observable, Subject, take } from 'rxjs';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });
  private readonly options = { headers: this.headers };
  private accessToken = '';

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private router: Router,
  ) {
    if (localStorage.getItem('gpf-token')) {
      this.accessToken = localStorage.getItem('gpf-token');
    }
  }

  public getAccessToken(): string {
    return this.accessToken;
  }

  public requestAccessToken(code: string): Subject<boolean> {
    const tokenObservable = this.http.post(this.config.rootUrl + '/o/token/', {
      client_id: 'TgvqlBwtPEor9AoizuuLQQ06ZwXNzC74n9Og7Cfw',
      code: code,
      grant_type: 'authorization_code',
      code_verifier: 'MTIz', //TODO: Fix this, use proper code verifier (must be fixed in users.component.ts as well)
    }, this.options);

    const exchangeSubject = new Subject<boolean>();

    tokenObservable.pipe(take(1)).subscribe(res => {
      this.accessToken = res['access_token'];
      localStorage.setItem('gpf-token', this.accessToken);
      // Remove auth code from query params and refresh navigation
      this.router.navigate([], {
        queryParams: {'code': null},
        queryParamsHandling: 'merge'
      })
    });

    return exchangeSubject; // TODO: Could be redone with pipe
  }

  public revokeAccessToken(): Observable<object> {
    const revokeObservable = this.http.post(this.config.rootUrl + '/o/revoke_token/', {
      client_id: 'TgvqlBwtPEor9AoizuuLQQ06ZwXNzC74n9Og7Cfw',
      token: this.accessToken,
    }, this.options)

    revokeObservable.pipe(take(1)).subscribe(_ => { 
      this.accessToken = '';
      localStorage.removeItem('gpf-token');
    }); // TODO: Could be redone with pipe

    return revokeObservable;
  }
}
