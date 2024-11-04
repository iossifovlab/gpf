/* eslint @typescript-eslint/naming-convention: 0 */
import { Injectable, Inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ConfigService } from './config/config.service';
import { Observable, Subject, take, tap, catchError } from 'rxjs';
import { APP_BASE_HREF } from '@angular/common';
import { CookieService } from 'ngx-cookie-service';
import pkceChallenge from 'pkce-challenge';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });
  private readonly options = { headers: this.headers };
  public tokenExchangeSubject = new Subject<boolean>();

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private cookieService: CookieService,
    @Inject(APP_BASE_HREF) private baseHref: string,
  ) { }

  public get accessToken(): string {
    return this.cookieService.get('access_token') || '';
  }

  public get refreshAccessToken(): string {
    return localStorage.getItem('refresh_token') || '';
  }

  public generatePKCE(): string {
    const pkce = pkceChallenge();
    localStorage.setItem('code_verifier', pkce['code_verifier']);
    return pkce['code_challenge'];
  }

  public requestAccessToken(code: string): Observable<object> {
    return this.http.post(`${this.config.rootUrl}${this.baseHref}o/token/`, {
      client_id: this.config.oauthClientId,
      code: code,
      grant_type: 'authorization_code',
      redirect_uri: `${window.location.origin}${this.baseHref}login`,
      code_verifier: localStorage.getItem('code_verifier'),
    }, this.options).pipe(take(1), tap(res => {
      this.setTokens(res);
      localStorage.removeItem('code_verifier');
      this.tokenExchangeSubject.next(true);
    }));
  }

  public revokeAccessToken(): Observable<object> {
    return this.http.post(`${this.config.rootUrl}${this.baseHref}o/revoke_token/`, {
      client_id: this.config.oauthClientId,
      token: this.accessToken,
    }, this.options).pipe(take(1), tap({next: () => this.clearTokens()}));
  }

  public clearTokens(): void {
    this.cookieService.delete('access_token', '/');
    localStorage.removeItem('refresh_token');
  }

  public refreshToken(): Observable<object> {
    if (this.refreshAccessToken !== '') {
      return this.http.post(`${this.config.rootUrl}${this.baseHref}o/token/`, {
        grant_type: 'refresh_token',
        client_id: this.config.oauthClientId,
        refresh_token: this.refreshAccessToken,
      }, this.options).pipe(
        take(1),
        tap(res => {
          this.setTokens(res);
        }),
        catchError((err, caught) => {
          // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
          if (err.status === 500 || (err.status === 400 && err.error.error === 'invalid_grant')) {
            this.clearTokens();
            window.location.reload();
          }
          return caught;
        })
      );
    } else {
      this.clearTokens();
      window.location.reload();
    }
  }

  private setTokens(res: object): void {
    this.cookieService.set('access_token', res['access_token'] as string, {path: '/'});
    localStorage.setItem('refresh_token', res['refresh_token'] as string);
  }
}
