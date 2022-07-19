import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from './config/config.service';
import { Observable, Subject, take, tap } from 'rxjs';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });
  private readonly options = { headers: this.headers };
  private _accessToken = '';
  private _refreshToken = '';

  public tokenExchangeSubject = new Subject<boolean>();

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private router: Router,
  ) {
    this._accessToken = localStorage.getItem('access_token') || '';
    this._refreshToken = localStorage.getItem('refresh_token') || '';
  }

  public getAccessToken(): string {
    return this._accessToken;
  }

  public requestAccessToken(code: string): Observable<object> {
    return this.http.post(this.config.rootUrl + '/o/token/', {
      client_id: this.config.oauthClientId,
      code: code,
      grant_type: 'authorization_code',
      code_verifier: 'MTIz', //TODO: Fix this, use proper code verifier (must be fixed in users.component.ts as well)
    }, this.options).pipe(take(1), tap(res => {
      this.setTokens(res);
      // Remove auth code from query params and refresh navigation
      this.router.navigate([], {
        queryParams: {'code': null},
        queryParamsHandling: 'merge'
      })
      this.tokenExchangeSubject.next(true);
    }));
  }

  public revokeAccessToken(): Observable<object> {
    return this.http.post(this.config.rootUrl + '/o/revoke_token/', {
      client_id: this.config.oauthClientId,
      token: this._accessToken,
    }, this.options).pipe(take(1), tap(_ => { 
      this._accessToken = '';
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }));
  }

  public refreshToken(): Observable<object> {
    if (this._refreshToken !== '') {
      return this.http.post(this.config.rootUrl + '/o/token/', {
        grant_type: 'refresh_token',
        client_id: this.config.oauthClientId,
        refresh_token: this._refreshToken,
      }, this.options).pipe(take(1), tap(res => {
        this.setTokens(res);
      }));
    }
  }

  private setTokens(res: object): void {
    this._accessToken = res['access_token'];
    this._refreshToken = res['refresh_token'];
    localStorage.setItem('access_token', this._accessToken);
    localStorage.setItem('refresh_token', this._refreshToken);
  }
}
