/* eslint @typescript-eslint/naming-convention: 0 */
import { Injectable, Inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ConfigService } from './config/config.service';
import { Observable, take, tap, catchError } from 'rxjs';
import { APP_BASE_HREF } from '@angular/common';
import { CookieService } from 'ngx-cookie-service';
import pkceChallenge from 'pkce-challenge';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/x-www-form-urlencoded' });
  private readonly options = { headers: this.headers };

  private authToken: string = null;

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private cookieService: CookieService,
    @Inject(APP_BASE_HREF) private baseHref: string,
  ) { }

  public get accessToken(): string {
    return this.authToken || '';
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
    const params = new HttpParams({fromObject: {
      client_id: this.config.oauthClientId,
      code: code,
      grant_type: 'authorization_code',
      redirect_uri: `${window.location.origin}${this.baseHref}login`,
      code_verifier: localStorage.getItem('code_verifier'),
    }});

    return this.http.post(
      `${this.config.rootUrl}${this.baseHref}o/token/`, params, this.options,
    ).pipe(take(1), tap(res => {
      this.setTokens(res);
      localStorage.removeItem('code_verifier');
    }));
  }

  public revokeAccessToken(): Observable<object> {
    const params = new HttpParams({fromObject: {
      client_id: this.config.oauthClientId,
      token: this.authToken,
    }});
    return this.http.post(
      `${this.config.rootUrl}${this.baseHref}o/revoke_token/`, params, this.options,
    );
  }

  public clearTokens(): void {
    this.cookieService.delete('access_token', '/');
    localStorage.removeItem('refresh_token');
  }

  public refreshToken(): Observable<object> {
    const params = new HttpParams({fromObject: {
      grant_type: 'refresh_token',
      client_id: this.config.oauthClientId,
      refresh_token: this.refreshAccessToken,
    }});

    if (this.refreshAccessToken !== '') {
      return this.http.post(
        `${this.config.rootUrl}${this.baseHref}o/token/`, params, this.options
      ).pipe(
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
    this.authToken = res['access_token'] as string;
    /* Storing the access token as a cookie allows authentication of requests
       where setting the Authorization header is not possible, as the backend is
       configured to look for the token in both the Authorization header and the cookies. */
    this.cookieService.set('access_token', this.authToken, {path: '/'});
    localStorage.setItem('refresh_token', res['refresh_token'] as string);
  }
}
