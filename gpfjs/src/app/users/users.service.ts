import { Observable, Subject } from 'rxjs';
import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
import { CookieService } from 'ngx-cookie-service';
import { User, UserInfo } from './users';
import { catchError, map, tap, take, switchMap } from 'rxjs/operators';
import { AuthService } from '../auth.service';
import {
  FederationCredential,
  FederationGetJson,
  FederationPostJson
} from 'app/federation-credentials/federation-credentials';
import { LocationStrategy } from '@angular/common';

@Injectable()
export class UsersService {
  private readonly logoutUrl = 'users/logout';
  private readonly userInfoUrl = 'users/get_user_info';
  private readonly resetPasswordUrl = 'users/forgotten_password';
  private readonly usersUrl = 'users';

  private lastUserInfo: UserInfo = null;

  public usersStreamingFinishedSubject = new Subject();

  /* This is used to indicate that the app is in the middle of logging out.
     Currently used by the AuthInterceptor to avoid interrupting the logout process. */
  public isLoggingOut = false;

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private cookieService: CookieService,
    private authService: AuthService,
    private locationStrategy: LocationStrategy
  ) { }

  public logout(): Observable<object> {
    const csrfToken = this.cookieService.get('csrftoken');
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    this.isLoggingOut = true;

    return this.http.post(this.config.baseUrl + this.logoutUrl, {}, options).pipe(
      take(1),
      switchMap(() => this.authService.revokeAccessToken()),
      tap(() => {
        this.authService.clearTokens();
        window.location.href = this.locationStrategy.getBaseHref();
      })
    );
  }

  public cachedUserInfo(): UserInfo {
    return this.lastUserInfo;
  }

  public getUserInfo(): Observable<UserInfo> {
    const options = { withCredentials: true };

    return this.http.get<UserInfo>(this.config.baseUrl + this.userInfoUrl, options).pipe(
      map(res => res),
      tap((userInfo: UserInfo) => {
        this.lastUserInfo = userInfo;
      })
    );
  }

  public resetPassword(email: string): void {
    const csrfToken = this.cookieService.get('csrftoken');
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const headers = { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json'};

    // Using plain js fetch, because the API end-point does not return JSON
    fetch(
      this.config.baseUrl + this.resetPasswordUrl,
      { body: JSON.stringify({ email: email }), headers: headers, credentials: 'include', method: 'POST'}
    );
  }

  public getAllUsers(): Observable<User[]> {
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + this.usersUrl, options).pipe(
      map(response => User.fromJsonArray(response))
    );
  }

  public getUser(id: number): Observable<User> {
    const options = { withCredentials: true };
    const url = `${this.config.baseUrl}${this.usersUrl}/${id}`;

    return this.http.get(url, options).pipe(
      map(response => User.fromJson(response))
    );
  }

  public updateUser(user: User): Observable<object> {
    if (!user.id) {
      return;
    }

    const dto = {
      id: user.id,
      name: user.name,
      groups: user.groups,
      hasPassword: user.hasPassword,
    };

    const csrfToken = this.cookieService.get('csrftoken');
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}`;

    return this.http.put(url, dto, options);
  }

  public createUser(user: User): Observable<User> {
    // id is backend generated - remove if present at creation
    user.id = null;

    const csrfToken = this.cookieService.get('csrftoken');
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.usersUrl, user, options).pipe(
      map(response => User.fromJson(response)),
      catchError((error: HttpErrorResponse) => {
        // eslint-disable-next-line @typescript-eslint/only-throw-error
        throw error;
      })
    );
  }

  public deleteUser(user: User): Observable<object> {
    if (!user.id) {
      return;
    }
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}`;
    const options = { withCredentials: true };

    return this.http.delete(url, options);
  }

  public removeUserGroup(user: User, group: string): Observable<object> {
    const clone = user.clone();
    clone.groups = clone.groups.filter(grp => grp !== group);
    return this.updateUser(clone);
  }

  public getUsers(page: number, searchTerm: string): Observable<User[]> {
    let url = `${this.config.baseUrl}${this.usersUrl}?page=${page}`;
    if (searchTerm) {
      const searchParams = new HttpParams().set('search', searchTerm);
      url += `&${searchParams.toString()}`;
    }

    const options = { withCredentials: true };

    return this.http.get<User[]>(url, options).pipe(
      map((response) => {
        if (response === null) {
          return [] as User[];
        }
        return response.map(user => {
          const usr = User.fromJson(user);
          // Finding and fixing duplicate dataset names
          usr.allowedDatasets.forEach(dataset => {
            const allOccurences = usr.allowedDatasets.filter(d => d.datasetName === dataset.datasetName);
            if (allOccurences.length > 1) {
              allOccurences.forEach(d => {
                d.datasetName += `(${d.datasetId})`;
              });
            }
          });
          return usr;
        });
      })
    );
  }

  public getFederationCredentials(): Observable<FederationCredential[]> {
    const options = { withCredentials: true };
    return this.http.get<FederationGetJson[]>(
      this.config.baseUrl + 'users/federation_credentials', options
    ).pipe(map(res => FederationCredential.fromJsonArray(res)));
  }

  public createFederationCredentials(credentialName: string): Observable<FederationPostJson> {
    const options = { withCredentials: true };
    return this.http.post<FederationPostJson>(
      this.config.baseUrl + 'users/federation_credentials',
      { name: credentialName },
      options
    ).pipe(
      map((res: FederationPostJson) => ({
        credentials: res.credentials,
        client_secret: res.client_secret,
        client_id: res.client_id,
      }))
    );
  }

  public updateFederationCredentials(oldCredentialName: string, newCredentialName: string): Observable<string> {
    const options = { withCredentials: true };

    return this.http.put(this.config.baseUrl + 'users/federation_credentials',
      // eslint-disable-next-line @typescript-eslint/naming-convention
      {name: oldCredentialName, new_name: newCredentialName}, options)
      .pipe(
        // eslint-disable-next-line @typescript-eslint/naming-convention
        map((res: {new_name: string}) => res.new_name)
      );
  }

  public deleteFederationCredentials(credentialName: string): Observable<object> {
    const options = { withCredentials: true, body: { name: credentialName }};

    return this.http.delete(this.config.baseUrl + 'users/federation_credentials', options);
  }
}
