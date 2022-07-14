
import {throwError as observableThrowError, Observable, Subject, ReplaySubject, of, BehaviorSubject } from 'rxjs';
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { ConfigService } from '../config/config.service';
import { CookieService } from 'ngx-cookie-service';
import { User } from './users';
import { LocationStrategy } from '@angular/common';
import { Store } from '@ngxs/store';
import { StateResetAll } from 'ngxs-reset-plugin';
import { catchError, map, tap, take } from 'rxjs/operators';
import { AuthService } from '../auth.service';
const oboe = require('oboe');

@Injectable()
export class UsersService {
  private readonly logoutUrl = 'users/logout';
  private readonly userInfoUrl = 'users/get_user_info';
  private readonly registerUrl = 'users/register';
  private readonly resetPasswordUrl = 'users/reset_password';
  private readonly changePasswordUrl = 'users/change_password';
  private readonly checkVerificationUrl = 'users/check_verif_path';
  private readonly usersUrl = 'users';
  private readonly usersStreamingUrl = `${this.usersUrl}/streaming_search`;

  private userInfo$ = new ReplaySubject<{}>(1);
  private lastUserInfo = null;

  public usersStreamingFinishedSubject = new Subject();
  public emailLog: BehaviorSubject<string>;

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
    private cookieService: CookieService,
    private store: Store,
    private locationStrategy: LocationStrategy,
    private authService: AuthService,
  ) {
    this.emailLog = new BehaviorSubject('');
    this.authService.tokenExchangeSubject.subscribe(() => {
      // Refresh user data when a token arrives
      this.getUserInfo().pipe(take(1)).subscribe(() => {});
    });
  }

  public logout(): Observable<boolean> {
    return this.authService.revokeAccessToken().pipe(
      map(() => {
        this.store.dispatch(new StateResetAll());
        window.location.href = this.locationStrategy.getBaseHref();
        return true;
      })
    );
  }

  public cachedUserInfo() {
    return this.lastUserInfo;
  }

  public getUserInfoObservable(): Observable<any> {
    return this.userInfo$.asObservable();
  }

  public getUserInfo(): Observable<any> {
    const options = { withCredentials: true };

    return this.http.get(this.config.baseUrl + this.userInfoUrl, options).pipe(
      map(res => res),
      tap(userInfo => {
        this.userInfo$.next(userInfo);
        this.lastUserInfo = userInfo;
      })
    );
  }

  public isEmailValid(email: string): boolean {
    const re = new RegExp(
      "[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{" +
      "|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?" +
      ":[a-z0-9-]*[a-z0-9])?"
    );
    return re.test(String(email).toLowerCase());
  }

  public isNameValid(name: string): boolean {
    return !(name === undefined || name === '');
  }

  public register(email: string, name: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    if (!this.isEmailValid(email)) {
      return observableThrowError(new Error(
        'Invalid email address entered. Please use a valid email address.'
      ));
    }

    if (!this.isNameValid(name)) {
      return observableThrowError(new Error(
        'Name field cannot be empty.'
      ));
    }

    return this.http.post(this.config.baseUrl + this.registerUrl, {
      email: email,
      name: name,
    }, options).pipe(
      map(() => true),
      catchError(error => {
        return observableThrowError(new Error(error.error.error_msg));
      })
    );
  }

  public resetPassword(email: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    if (!this.isEmailValid(email)) {
      return observableThrowError(new Error(
        'Invalid email address entered. Please use a valid email address.'
      ));
    }

    return this.http.post(this.config.baseUrl + this.resetPasswordUrl, { email: email }, options).pipe(
      map(() => true),
      catchError(error => {
        return observableThrowError(new Error(error.error.error_msg));
      })
    );
  }

  public changePassword(password: string, verifPath: string): Observable<boolean | object> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.changePasswordUrl, {
      password: password, verifPath: verifPath
    }, options).pipe(
      map(() => true),
      catchError(res => {
        return of({error: res.error.error_msg})
      })
    );
  }

  public checkVerification(verifPath: string): Observable<boolean> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.checkVerificationUrl, {
      verifPath: verifPath
    }, options).pipe(
      map(() => true),
      catchError(() => {
        return of(false);
      })
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
    const dto = {
      id: user.id,
      name: user.name,
      groups: user.groups,
      hasPassword: user.hasPassword,
    };
    if (!user.id) {
      return observableThrowError('Unknown id...');
    }
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}`;

    return this.http.put(url, dto, options);
  }

  public createUser(user: User): Observable<User> {
    if (user.id) {
      return observableThrowError('Create should not have user id');
    }

    if (!this.isEmailValid(user.email)) {
      return observableThrowError(new Error(
        'Invalid email address entered. Please use a valid email address.'
      ));
    }

    if (!this.isNameValid(user.name)) {
      return observableThrowError(new Error(
        'Name field cannot be empty.'
      ));
    }

    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const options = { headers: headers, withCredentials: true };

    return this.http.post(this.config.baseUrl + this.usersUrl, user, options).pipe(
      map(response => User.fromJson(response)),
      catchError(error => {
        return observableThrowError(new Error(error.error.email));
      })
    );
  }

  public deleteUser(user: User): Observable<object> {
    if (!user.id) {
      return observableThrowError('No user id');
    }
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}`;
    const options = { withCredentials: true };

    return this.http.delete(url, options);
  }

  public resetUserPassword(user: User): Observable<object> {
    if (!user.id) {
      return observableThrowError('No user id');
    }
    const url = `${this.config.baseUrl}${this.usersUrl}/${user.id}/password_reset`;
    const options = { withCredentials: true };

    return this.http.post(url, null, options);
  }

  public removeUserGroup(user: User, group: string): Observable<object> {
    const clone = user.clone();
    clone.groups = clone.groups.filter(grp => grp !== group);
    return this.updateUser(clone);
  }

  public searchUsersByGroup(searchTerm: string): Observable<User> {
    const csrfToken = this.cookieService.get('csrftoken');
    const headers = { 'X-CSRFToken': csrfToken };
    const usersSubject: Subject<User> = new Subject();

    let url: string;
    if (searchTerm !== null) {
      const searchParams = new HttpParams().set('search', searchTerm);
      url = `${this.config.baseUrl}${this.usersStreamingUrl}?${searchParams.toString()}`;
    } else {
      url = `${this.config.baseUrl}${this.usersStreamingUrl}`;
    }

    oboe({
      url: url,
      method: "GET",
      headers: headers,
      withCredentials: true,
    }).start(() => {
      this.usersStreamingFinishedSubject.next(false);
    }).node('!.*', data => {
      usersSubject.next(data);
    }).done(() => {
      this.usersStreamingFinishedSubject.next(true);
    }).fail(() => {
      this.usersStreamingFinishedSubject.next(true);
      console.warn('oboejs encountered a fail event while streaming');
    });

    return usersSubject.pipe(map(data => { return User.fromJson(data); }));
  }
}
